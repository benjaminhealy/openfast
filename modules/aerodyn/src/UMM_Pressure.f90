!**********************************************************************************************************************************
! UMM_Pressure Module
! Unified Momentum Model (UMM) Module for OpenFAST Implementation
!
! This module contains:
!   - Pressure table data for nonlinear pressure correction
!   - File I/O routines to read pressure table from external file
!   - Uses bilinear interpolation of pre-cached pressure lookup table
!
! Reference Paper: Liew et al. 2024 - https://www.nature.com/articles/s41467-024-50756-5
! Supplementary Information: https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-024-50756-5/MediaObjects/41467_2024_50756_MOESM1_ESM.pdf
! Code Source (Python): https://github.com/Howland-Lab/Unified-Momentum-Model/
!
!**********************************************************************************************************************************
module UMM_Pressure

   use NWTC_Library

   implicit none

   private

   !-------------------------------------------------------------------------------------------------
   ! Module state - indicates whether the module has been initialized
   !-------------------------------------------------------------------------------------------------
   logical, save :: m_Initialized = .false.

   !-------------------------------------------------------------------------------------------------
   ! Pressure table dimensions (read from file, stored as module variables)
   !-------------------------------------------------------------------------------------------------
   integer(IntKi), save, public :: UMM_N_DP = 0    ! Number of dp axis points
   integer(IntKi), save, public :: UMM_N_X  = 0    ! Number of x axis points

   !-------------------------------------------------------------------------------------------------
   ! Allocatable arrays for table data (populated by UMM_Pressure_Init)
   !-------------------------------------------------------------------------------------------------
   real(R8Ki), allocatable, save, public :: UMM_DP_VALS(:)     ! dp (CT/2) axis values
   real(R8Ki), allocatable, save, public :: UMM_X_VALS(:)      ! x (near-wake length) axis values
   real(R8Ki), allocatable, save, public :: UMM_P_TABLE(:,:)   ! Pressure table (N_DP x N_X)

   ! Public interface
   public :: UMM_Pressure_Init
   public :: UMM_Pressure_End
   public :: interpolatePressureTable
   public :: UMM_Pressure_IsInitialized

contains

   !> Check if the module has been initialized
   function UMM_Pressure_IsInitialized() result(isInit)
      logical :: isInit
      isInit = m_Initialized
   end function UMM_Pressure_IsInitialized

   !> Initialize the UMM pressure table by reading from an external file
   !! @param PressureFile Path to the UMM pressure table file
   !! @param ErrStat Error status (0 = success)
   !! @param ErrMsg Error message
   subroutine UMM_Pressure_Init(PressureFile, ErrStat, ErrMsg)
      character(*), intent(in)    :: PressureFile   !< Path to pressure table file
      integer(IntKi), intent(out) :: ErrStat        !< Error status
      character(*), intent(out)   :: ErrMsg         !< Error message

      ! Local variables
      integer(IntKi) :: UnIn                  ! Unit number for file I/O
      integer(IntKi) :: ErrStat2              ! Temporary error status
      character(ErrMsgLen) :: ErrMsg2         ! Temporary error message
      character(4096) :: Line                 ! Line buffer (must be large enough for X axis with many values)
      integer(IntKi) :: i, j                  ! Loop indices
      integer(IntKi) :: NumDP, NumX           ! Table dimensions from file
      real(R8Ki), allocatable :: TempRow(:)   ! Temporary row for reading

      ! Initialize error handling
      ErrStat = ErrID_None
      ErrMsg = ''

      ! Check if already initialized
      if (m_Initialized) then
         call UMM_Pressure_End()  ! Clean up previous initialization
      endif

      ! Check for empty filename
      if (len_trim(PressureFile) == 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: UMM_PressureFile is empty. A pressure table file is required when SkewMomCorr=2 (UMM).'
         return
      endif

      ! Get a free unit number
      call GetNewUnit(UnIn, ErrStat2, ErrMsg2)
      if (ErrStat2 /= ErrID_None) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Could not get unit number: '//trim(ErrMsg2)
         return
      endif

      ! Open the file
      call OpenFInpFile(UnIn, PressureFile, ErrStat2, ErrMsg2)
      if (ErrStat2 /= ErrID_None) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Could not open file "'//trim(PressureFile)//'": '//trim(ErrMsg2)
         return
      endif

      ! Skip header lines (lines starting with ! or -)
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Pressure_Init: Error reading header from "'//trim(PressureFile)//'"'
            close(UnIn)
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read NumDP (first data line after headers)
      read(Line, *, iostat=ErrStat2) NumDP
      if (ErrStat2 /= 0 .or. NumDP <= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Invalid NumDP value in "'//trim(PressureFile)//'"'
         close(UnIn)
         return
      endif

      ! Skip to next data line
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Pressure_Init: Error reading NumX from "'//trim(PressureFile)//'"'
            close(UnIn)
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read NumX
      read(Line, *, iostat=ErrStat2) NumX
      if (ErrStat2 /= 0 .or. NumX <= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Invalid NumX value in "'//trim(PressureFile)//'"'
         close(UnIn)
         return
      endif

      ! Store dimensions
      UMM_N_DP = NumDP
      UMM_N_X = NumX

      ! Allocate arrays
      allocate(UMM_DP_VALS(NumDP), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Could not allocate UMM_DP_VALS'
         close(UnIn)
         return
      endif

      allocate(UMM_X_VALS(NumX), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Could not allocate UMM_X_VALS'
         close(UnIn)
         call UMM_Pressure_End()
         return
      endif

      allocate(UMM_P_TABLE(NumDP, NumX), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Could not allocate UMM_P_TABLE'
         close(UnIn)
         call UMM_Pressure_End()
         return
      endif

      allocate(TempRow(NumDP), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Could not allocate TempRow'
         close(UnIn)
         call UMM_Pressure_End()
         return
      endif

      ! Skip to DP axis values section
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Pressure_Init: Error finding DP axis section in "'//trim(PressureFile)//'"'
            close(UnIn)
            call UMM_Pressure_End()
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read DP axis values
      read(Line, *, iostat=ErrStat2) (UMM_DP_VALS(i), i=1, NumDP)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Error reading DP axis values from "'//trim(PressureFile)//'"'
         close(UnIn)
         call UMM_Pressure_End()
         return
      endif

      ! Skip to X axis values section
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Pressure_Init: Error finding X axis section in "'//trim(PressureFile)//'"'
            close(UnIn)
            call UMM_Pressure_End()
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read X axis values
      read(Line, *, iostat=ErrStat2) (UMM_X_VALS(i), i=1, NumX)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Error reading X axis values from "'//trim(PressureFile)//'"'
         close(UnIn)
         call UMM_Pressure_End()
         return
      endif

      ! Skip to pressure table section
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Pressure_Init: Error finding pressure table section in "'//trim(PressureFile)//'"'
            close(UnIn)
            call UMM_Pressure_End()
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read pressure table (one row per X value, NumDP values per row)
      ! First row was already read into Line
      read(Line, *, iostat=ErrStat2) (TempRow(i), i=1, NumDP)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Pressure_Init: Error reading pressure table row 1 from "'//trim(PressureFile)//'"'
         close(UnIn)
         call UMM_Pressure_End()
         return
      endif
      UMM_P_TABLE(:, 1) = TempRow

      ! Read remaining rows
      do j = 2, NumX
         read(UnIn, *, iostat=ErrStat2) (TempRow(i), i=1, NumDP)
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            write(ErrMsg, '(A,I0,A)') 'UMM_Pressure_Init: Error reading pressure table row ', j, &
                                      ' from "'//trim(PressureFile)//'"'
            close(UnIn)
            call UMM_Pressure_End()
            return
         endif
         UMM_P_TABLE(:, j) = TempRow
      end do

      ! Cleanup
      close(UnIn)
      deallocate(TempRow)

      m_Initialized = .true.

   end subroutine UMM_Pressure_Init


   !> Clean up the UMM pressure module (deallocate arrays)
   subroutine UMM_Pressure_End()

      if (allocated(UMM_DP_VALS)) deallocate(UMM_DP_VALS)
      if (allocated(UMM_X_VALS))  deallocate(UMM_X_VALS)
      if (allocated(UMM_P_TABLE)) deallocate(UMM_P_TABLE)

      UMM_N_DP = 0
      UMM_N_X = 0
      m_Initialized = .false.

   end subroutine UMM_Pressure_End


   !> Bilinear interpolation of the nonlinear pressure table for UMM
   !! Returns the nonlinear pressure correction p_g at given (dp_half, x0)
   !! @param dp_half CT/2 value (row index into table)
   !! @param x0 Near-wake length (column index into table)
   !! @return p_g nonlinear pressure correction
   function interpolatePressureTable(dp_half, x0) result(p_g)
      implicit none
      real(R8Ki), intent(in) :: dp_half    !< CT/2 value (row index into table)
      real(R8Ki), intent(in) :: x0         !< Near-wake length (column index into table)
      real(R8Ki) :: p_g                    !< Nonlinear pressure correction (output)

      integer(IntKi) :: i_dp, i_x          ! Grid indices
      real(R8Ki) :: frac_dp, frac_x        ! Interpolation fractions
      real(R8Ki) :: p11, p12, p21, p22     ! Corner values
      real(R8Ki) :: dp_clamped, x_clamped  ! Clamped input values

      ! Check if module is initialized
      if (.not. m_Initialized) then
         p_g = 0.0_R8Ki
         return
      endif

      ! Clamp values to table bounds (extrapolate using edge values for out-of-bounds inputs)
      ! This avoids discontinuities at table boundaries, especially for tip conditions
      ! where x0 may exceed the table range due to low local loading
      dp_clamped = max(UMM_DP_VALS(1), min(UMM_DP_VALS(UMM_N_DP), dp_half))
      x_clamped  = max(UMM_X_VALS(1),  min(UMM_X_VALS(UMM_N_X),  x0))

      ! Find bracketing indices for dp axis (lookup axis monotonically increases w/ uniform spacing)
      i_dp = int((dp_clamped - UMM_DP_VALS(1)) / (UMM_DP_VALS(2) - UMM_DP_VALS(1))) + 1
      i_dp = max(1, min(i_dp, UMM_N_DP - 1))

      ! Find bracketing indices for x axis (lookup axis monotonically increases w/ uniform spacing)
      i_x = int((x_clamped - UMM_X_VALS(1)) / (UMM_X_VALS(2) - UMM_X_VALS(1))) + 1
      i_x = max(1, min(i_x, UMM_N_X - 1))

      ! Compute interpolation fractions (bilinear interpolation over uniformly spaced axes)
      if (i_dp < UMM_N_DP) then
         frac_dp = (dp_clamped - UMM_DP_VALS(i_dp)) / &
                   (UMM_DP_VALS(i_dp+1) - UMM_DP_VALS(i_dp))
      else
         frac_dp = 0.0_R8Ki
      endif

      if (i_x < UMM_N_X) then
         frac_x = (x_clamped - UMM_X_VALS(i_x)) / &
                  (UMM_X_VALS(i_x+1) - UMM_X_VALS(i_x))
      else
         frac_x = 0.0_R8Ki
      endif

      ! Get corner values surrounding interpolation point
      p11 = UMM_P_TABLE(i_dp, i_x)
      p12 = UMM_P_TABLE(i_dp, min(i_x+1, UMM_N_X))
      p21 = UMM_P_TABLE(min(i_dp+1, UMM_N_DP), i_x)
      p22 = UMM_P_TABLE(min(i_dp+1, UMM_N_DP), min(i_x+1, UMM_N_X))

      ! Bilinear interpolation
      p_g = (1.0_R8Ki - frac_dp) * ((1.0_R8Ki - frac_x) * p11 + frac_x * p12) + &
            frac_dp * ((1.0_R8Ki - frac_x) * p21 + frac_x * p22)

   end function interpolatePressureTable

end module UMM_Pressure
