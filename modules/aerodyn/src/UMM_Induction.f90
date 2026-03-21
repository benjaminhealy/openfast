!**********************************************************************************************************************************
! UMM_Induction Module
! Unified Momentum Model (UMM) tabulated induction lookup for OpenFAST
!
! This module contains:
!   - Pre-computed induction table data: (CT, yaw) -> an
!   - File I/O routines to read induction table from external file
!   - Uses bilinear interpolation of pre-cached induction lookup table
!
! Ref: Liew et al. 2024 (doi:10.1038/s41467-024-50756-5)
! Ref: MITRotor git repo (Howland-Lab/Unified-Momentum-Model)
!
!**********************************************************************************************************************************
module UMM_Induction

   use NWTC_Library

   implicit none

   private

   !-------------------------------------------------------------------------------------------------
   ! Module state - indicates whether the module has been initialized
   !-------------------------------------------------------------------------------------------------
   logical, save :: m_Initialized = .false.

   !-------------------------------------------------------------------------------------------------
   ! Induction table dimensions (read from file, stored as module variables)
   !-------------------------------------------------------------------------------------------------
   integer(IntKi), save, public :: UMM_IND_N_CT  = 0    ! Number of CT axis points
   integer(IntKi), save, public :: UMM_IND_N_YAW = 0    ! Number of yaw axis points

   !-------------------------------------------------------------------------------------------------
   ! Allocatable arrays for table data (populated by UMM_Induction_Init)
   !-------------------------------------------------------------------------------------------------
   real(R8Ki), allocatable, save, public :: UMM_IND_CT_VALS(:)    ! CT axis values
   real(R8Ki), allocatable, save, public :: UMM_IND_YAW_VALS(:)   ! Effective yaw axis values [rad]
   real(R8Ki), allocatable, save, public :: UMM_IND_TABLE(:,:)    ! Induction table (N_CT x N_YAW)

   ! Public interface
   public :: UMM_Induction_Init
   public :: UMM_Induction_End
   public :: interpolateInductionTable
   public :: UMM_Induction_IsInitialized

contains

   !> Check if the module has been initialized
   function UMM_Induction_IsInitialized() result(isInit)
      logical :: isInit
      isInit = m_Initialized
   end function UMM_Induction_IsInitialized

   !> Initialize the UMM induction table by reading from an external file
   !! @param InductionFile Path to the UMM induction table file
   !! @param ErrStat Error status (0 = success)
   !! @param ErrMsg Error message
   subroutine UMM_Induction_Init(InductionFile, ErrStat, ErrMsg)
      character(*), intent(in)    :: InductionFile  !< Path to induction table file
      integer(IntKi), intent(out) :: ErrStat        !< Error status
      character(*), intent(out)   :: ErrMsg         !< Error message

      ! Local variables
      integer(IntKi) :: UnIn                  ! Unit number for file I/O
      integer(IntKi) :: ErrStat2              ! Temporary error status
      character(ErrMsgLen) :: ErrMsg2         ! Temporary error message
      character(16384) :: Line                ! Line buffer (must be large for 1001 CT values)
      integer(IntKi) :: i, j                  ! Loop indices
      integer(IntKi) :: NumCT, NumYaw         ! Table dimensions from file
      real(R8Ki), allocatable :: TempRow(:)   ! Temporary row for reading

      ! Initialize error handling
      ErrStat = ErrID_None
      ErrMsg = ''

      ! Check if already initialized
      if (m_Initialized) then
         call UMM_Induction_End()
      endif

      ! Check for empty filename
      if (len_trim(InductionFile) == 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: UMM_InductionFile is empty. An induction table file is required when SkewMomCorr=3.'
         return
      endif

      ! Get a free unit number
      call GetNewUnit(UnIn, ErrStat2, ErrMsg2)
      if (ErrStat2 /= ErrID_None) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Could not get unit number: '//trim(ErrMsg2)
         return
      endif

      ! Open the file
      call OpenFInpFile(UnIn, InductionFile, ErrStat2, ErrMsg2)
      if (ErrStat2 /= ErrID_None) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Could not open file "'//trim(InductionFile)//'": '//trim(ErrMsg2)
         return
      endif

      ! Skip header lines (lines starting with ! or -)
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Induction_Init: Error reading header from "'//trim(InductionFile)//'"'
            close(UnIn)
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read NumCT (first data line after headers)
      read(Line, *, iostat=ErrStat2) NumCT
      if (ErrStat2 /= 0 .or. NumCT <= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Invalid NumCT value in "'//trim(InductionFile)//'"'
         close(UnIn)
         return
      endif

      ! Skip to next data line
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Induction_Init: Error reading NumYaw from "'//trim(InductionFile)//'"'
            close(UnIn)
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read NumYaw
      read(Line, *, iostat=ErrStat2) NumYaw
      if (ErrStat2 /= 0 .or. NumYaw <= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Invalid NumYaw value in "'//trim(InductionFile)//'"'
         close(UnIn)
         return
      endif

      ! Store dimensions
      UMM_IND_N_CT  = NumCT
      UMM_IND_N_YAW = NumYaw

      ! Allocate arrays
      allocate(UMM_IND_CT_VALS(NumCT), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Could not allocate UMM_IND_CT_VALS'
         close(UnIn)
         return
      endif

      allocate(UMM_IND_YAW_VALS(NumYaw), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Could not allocate UMM_IND_YAW_VALS'
         close(UnIn)
         call UMM_Induction_End()
         return
      endif

      allocate(UMM_IND_TABLE(NumCT, NumYaw), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Could not allocate UMM_IND_TABLE'
         close(UnIn)
         call UMM_Induction_End()
         return
      endif

      allocate(TempRow(NumCT), stat=ErrStat2)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Could not allocate TempRow'
         close(UnIn)
         call UMM_Induction_End()
         return
      endif

      ! Skip to CT axis values section
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Induction_Init: Error finding CT axis section in "'//trim(InductionFile)//'"'
            close(UnIn)
            call UMM_Induction_End()
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read CT axis values
      read(Line, *, iostat=ErrStat2) (UMM_IND_CT_VALS(i), i=1, NumCT)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Error reading CT axis values from "'//trim(InductionFile)//'"'
         close(UnIn)
         call UMM_Induction_End()
         return
      endif

      ! Skip to yaw axis values section
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Induction_Init: Error finding yaw axis section in "'//trim(InductionFile)//'"'
            close(UnIn)
            call UMM_Induction_End()
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read yaw axis values
      read(Line, *, iostat=ErrStat2) (UMM_IND_YAW_VALS(i), i=1, NumYaw)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Error reading yaw axis values from "'//trim(InductionFile)//'"'
         close(UnIn)
         call UMM_Induction_End()
         return
      endif

      ! Skip to induction table section
      do
         read(UnIn, '(A)', iostat=ErrStat2) Line
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            ErrMsg = 'UMM_Induction_Init: Error finding induction table section in "'//trim(InductionFile)//'"'
            close(UnIn)
            call UMM_Induction_End()
            return
         endif
         Line = adjustl(Line)
         if (Line(1:1) /= '!' .and. Line(1:1) /= '-' .and. len_trim(Line) > 0) exit
      end do

      ! Read induction table (one row per yaw value, NumCT values per row)
      ! First row was already read into Line
      read(Line, *, iostat=ErrStat2) (TempRow(i), i=1, NumCT)
      if (ErrStat2 /= 0) then
         ErrStat = ErrID_Fatal
         ErrMsg = 'UMM_Induction_Init: Error reading induction table row 1 from "'//trim(InductionFile)//'"'
         close(UnIn)
         call UMM_Induction_End()
         return
      endif
      UMM_IND_TABLE(:, 1) = TempRow

      ! Read remaining rows
      do j = 2, NumYaw
         read(UnIn, *, iostat=ErrStat2) (TempRow(i), i=1, NumCT)
         if (ErrStat2 /= 0) then
            ErrStat = ErrID_Fatal
            write(ErrMsg, '(A,I0,A)') 'UMM_Induction_Init: Error reading induction table row ', j, &
                                      ' from "'//trim(InductionFile)//'"'
            close(UnIn)
            call UMM_Induction_End()
            return
         endif
         UMM_IND_TABLE(:, j) = TempRow
      end do

      ! Cleanup
      close(UnIn)
      deallocate(TempRow)

      m_Initialized = .true.

   end subroutine UMM_Induction_Init


   !> Clean up the UMM induction module (deallocate arrays)
   subroutine UMM_Induction_End()

      if (allocated(UMM_IND_CT_VALS))  deallocate(UMM_IND_CT_VALS)
      if (allocated(UMM_IND_YAW_VALS)) deallocate(UMM_IND_YAW_VALS)
      if (allocated(UMM_IND_TABLE))    deallocate(UMM_IND_TABLE)

      UMM_IND_N_CT  = 0
      UMM_IND_N_YAW = 0
      m_Initialized = .false.

   end subroutine UMM_Induction_End


   !> Bilinear interpolation of the UMM induction table
   !! Returns the axial induction factor an at given (CT, eff_yaw)
   !! @param CT Thrust coefficient
   !! @param eff_yaw Effective yaw angle [rad]
   !! @return an Axial induction factor
   function interpolateInductionTable(CT, eff_yaw) result(an)
      implicit none
      real(R8Ki), intent(in) :: CT          !< Thrust coefficient
      real(R8Ki), intent(in) :: eff_yaw     !< Effective yaw angle [rad]
      real(R8Ki) :: an                      !< Axial induction factor (output)

      integer(IntKi) :: i_ct, i_yaw            ! Grid indices
      real(R8Ki) :: frac_ct, frac_yaw          ! Interpolation fractions
      real(R8Ki) :: a11, a12, a21, a22         ! Corner values
      real(R8Ki) :: ct_clamped, yaw_clamped    ! Clamped input values

      ! Check if module is initialized
      if (.not. m_Initialized) then
         an = 0.0_R8Ki
         return
      endif

      ! Clamp values to table bounds
      ct_clamped  = max(UMM_IND_CT_VALS(1),  min(UMM_IND_CT_VALS(UMM_IND_N_CT),   CT))
      yaw_clamped = max(UMM_IND_YAW_VALS(1), min(UMM_IND_YAW_VALS(UMM_IND_N_YAW), eff_yaw))

      ! Find bracketing indices for CT axis (uniform spacing)
      i_ct = int((ct_clamped - UMM_IND_CT_VALS(1)) / (UMM_IND_CT_VALS(2) - UMM_IND_CT_VALS(1))) + 1
      i_ct = max(1, min(i_ct, UMM_IND_N_CT - 1))

      ! Find bracketing indices for yaw axis (uniform spacing)
      i_yaw = int((yaw_clamped - UMM_IND_YAW_VALS(1)) / (UMM_IND_YAW_VALS(2) - UMM_IND_YAW_VALS(1))) + 1
      i_yaw = max(1, min(i_yaw, UMM_IND_N_YAW - 1))

      ! Compute interpolation fractions
      if (i_ct < UMM_IND_N_CT) then
         frac_ct = (ct_clamped - UMM_IND_CT_VALS(i_ct)) / &
                   (UMM_IND_CT_VALS(i_ct+1) - UMM_IND_CT_VALS(i_ct))
      else
         frac_ct = 0.0_R8Ki
      endif

      if (i_yaw < UMM_IND_N_YAW) then
         frac_yaw = (yaw_clamped - UMM_IND_YAW_VALS(i_yaw)) / &
                    (UMM_IND_YAW_VALS(i_yaw+1) - UMM_IND_YAW_VALS(i_yaw))
      else
         frac_yaw = 0.0_R8Ki
      endif

      ! Get corner values surrounding interpolation point
      a11 = UMM_IND_TABLE(i_ct, i_yaw)
      a12 = UMM_IND_TABLE(i_ct, min(i_yaw+1, UMM_IND_N_YAW))
      a21 = UMM_IND_TABLE(min(i_ct+1, UMM_IND_N_CT), i_yaw)
      a22 = UMM_IND_TABLE(min(i_ct+1, UMM_IND_N_CT), min(i_yaw+1, UMM_IND_N_YAW))

      ! Bilinear interpolation
      an = (1.0_R8Ki - frac_ct) * ((1.0_R8Ki - frac_yaw) * a11 + frac_yaw * a12) + &
           frac_ct * ((1.0_R8Ki - frac_yaw) * a21 + frac_yaw * a22)

   end function interpolateInductionTable

end module UMM_Induction
