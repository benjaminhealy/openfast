!**********************************************************************************************************************************
! UMM_FixedPointIteration Module
! Unified Momentum Model (UMM) Module for OpenFAST Implementation
!
! This module contains:
!   - UMM iteration parameters (BETA, V4_CORR, MAX_ITER, TOLERANCE, RELAXATION)
!   - computeUMMResiduals6: Compute the 6 UMM residual equations
!   - getUMMInitialGuess: Get initial guess for UMM iteration
!
! Ref: Liew et al. 2024 (doi:10.1038/s41467-024-50756-5)
! Ref: MITRotor git repo (Howland-Lab/Unified-Momentum-Model)
!
!**********************************************************************************************************************************
module UMM_FixedPointIteration

   use NWTC_Library
   use UMM_Pressure

   implicit none

   private

   !-------------------------------------------------------------------------------------------------
   ! UMM Iteration Parameters
   !-------------------------------------------------------------------------------------------------
   integer(IntKi), public, parameter :: UMM_MAX_ITER_PER_STAGE = 25000         ! Maximum iterations per adaptive stage
   integer(IntKi), public, parameter :: UMM_NUM_STAGES = 2                     ! Number of adaptive relaxation stages
   real(R8Ki),     public, parameter :: UMM_RELAXATIONS(2) = [0.4_R8Ki, 0.6_R8Ki]  ! Relaxation factors per stage
   real(R8Ki),     public, parameter :: UMM_TOLERANCE = 1.0e-5_R8Ki            ! Convergence tolerance on residuals

   !-------------------------------------------------------------------------------------------------
   ! UMM Physical Constants
   !-------------------------------------------------------------------------------------------------
   real(R8Ki),     public, parameter :: UMM_BETA = 0.1403_R8Ki       ! Wake expansion parameter (empirical)
   real(R8Ki),     public, parameter :: UMM_V4_CORR = 1.0_R8Ki       ! Lateral velocity correction

   !-------------------------------------------------------------------------------------------------
   ! Public interface
   !-------------------------------------------------------------------------------------------------
   public :: computeUMMResiduals6
   public :: getUMMInitialGuess

contains

   !> Compute the 6 UMM residual equations (Liew et al. 2024, Eq. 1-6)
   !! State vector x = (an, u4, v4, x0, dp, Ctprime)
   subroutine computeUMMResiduals6(x, CT, k, F, eff_yaw, residuals)
      implicit none
      real(R8Ki), intent(in)  :: x(6)         !< x = (an, u4, v4, x0, dp, Ctprime)
      real(R8Ki), intent(in)  :: CT           !< Thrust coefficient from velocity-based formulation
      real(R8Ki), intent(in)  :: k            !< Thrust parameter from BEM (for logging only)
      real(ReKi), intent(in)  :: F            !< Tip/hub loss factor
      real(R8Ki), intent(in)  :: eff_yaw      !< Effective yaw angle [rad]
      real(R8Ki), intent(out) :: residuals(6) !< Output residuals

      ! Local variables (x) to solve via fixed point iteration
      real(R8Ki) :: an, u4, v4, x0_val, dp, Ctprime
      ! Intermediate calculations
      real(R8Ki) :: cos_eff_yaw, cos_eff_yaw2, sin_eff_yaw
      real(R8Ki) :: CT_used, CT_iter, dp_half, p_g, p_linear
      real(R8Ki) :: term1, term2_sqrt_arg, sqrt_arg1
      real(R8Ki) :: an_new, u4_new, v4_new, x0_new, dp_new, Ctprime_new

      ! Extract state variables (x)
      an      = x(1)
      u4      = x(2)    ! non-dimensionalized as fraction of u_inf
      v4      = x(3)    ! non-dimensionalized as fraction of u_inf
      x0_val  = x(4)
      dp      = x(5)
      Ctprime = x(6)

      ! Precompute trigonometric terms
      cos_eff_yaw  = cos(eff_yaw)
      cos_eff_yaw2 = cos_eff_yaw**2
      sin_eff_yaw  = sin(eff_yaw)

      ! Floor cos^2(yaw) to prevent division by zero
      if (cos_eff_yaw2 < 1.0e-10_R8Ki) then
         cos_eff_yaw2 = 1.0e-10_R8Ki
      endif

      ! Handle CT=0 scenario
      if (abs(Ctprime) < 1.0e-10_R8Ki) then
         residuals(1) = -an                  ! an = an - an = 0
         residuals(2) = 1.0_R8Ki - u4        ! u4 = u4 + (1 - u4) = 1
         residuals(3) = -v4                  ! v4 = v4 - v4 = 0
         residuals(4) = 100.0_R8Ki - x0_val  ! x0_val = x0_val + (100 - x0_val) = 100
         residuals(5) = -dp                  ! dp = dp - dp = 0
         residuals(6) = -Ctprime             ! Ctprime = Ctprime - Ctprime = 0
         return
      endif

      CT_used = CT
      CT_used = max(-4.0_R8Ki, min(CT_used, 10.0_R8Ki))

      ! Nonlinear pressure correction from lookup table
      ! CT_iter = Ctprime * (1-an)^2 * cos^2(yaw); dp_half = CT_iter / 2
      CT_iter = Ctprime * (1.0_R8Ki - an)**2 * cos_eff_yaw2
      CT_iter = max(-4.0_R8Ki, min(CT_iter, 10.0_R8Ki))  ! Clamp to reasonable bounds
      dp_half = CT_iter / 2.0_R8Ki

      ! Call bilinear interpolation of pre-cached nonlinear pressure table at dp and x0 indices
      p_g = interpolatePressureTable(dp_half, max(x0_val, 0.01_R8Ki))

      !------------------------------------------------------------------------
      ! Eq. 1: Rotor-normal induction (Liew et al. 2024)
      ! an = 1 - sqrt(-dp/(0.5*Ctprime*cos^2(yaw)) + (1-u4^2-v4^2)/(Ctprime*cos^2(yaw)))
      ! Velocities non-dimensionalized by u_inf; dp = delta_p / (rho * u_inf^2)
      !------------------------------------------------------------------------
      sqrt_arg1 = -dp / (0.5_R8Ki * Ctprime * cos_eff_yaw2) + &
                  (1.0_R8Ki - u4**2 - v4**2) / (Ctprime * cos_eff_yaw2)
      
      if (sqrt_arg1 >= 0.0_R8Ki) then
         an_new = 1.0_R8Ki - sqrt(sqrt_arg1)
      else
         an_new = an  ! Error handling: keep current value if sqrt argument is negative
      endif
      residuals(1) = an_new - an

      !------------------------------------------------------------------------
      ! Eq. 2: Streamwise outlet velocity (Liew et al. 2024)
      ! u4 = -0.25*Ctprime*(1-an)*cos^2(yaw) + 0.5 + 0.5*sqrt((0.5*Ctprime*(1-an)*cos^2(yaw)-1)^2 - 4*dp)
      !------------------------------------------------------------------------
      term1 = -0.25_R8Ki * Ctprime * (1.0_R8Ki - an) * cos_eff_yaw2
      term2_sqrt_arg = (0.5_R8Ki * Ctprime * (1.0_R8Ki - an) * cos_eff_yaw2 - 1.0_R8Ki)**2 - &
                       (4.0_R8Ki * dp)
      
      if (term2_sqrt_arg >= 0.0_R8Ki) then
         u4_new = term1 + 0.5_R8Ki + 0.5_R8Ki * sqrt(term2_sqrt_arg)
      else
         u4_new = u4  ! Error handling: keep current value if sqrt argument is negative
      endif
      residuals(2) = u4_new - u4

      !------------------------------------------------------------------------
      ! Eq. 3: Lateral outlet velocity (Liew et al. 2024)
      ! v4 = -v4_corr * 0.25 * Ctprime * (1-an)^2 * sin(yaw) * cos^2(yaw)
      !------------------------------------------------------------------------
      v4_new = -UMM_V4_CORR * 0.25_R8Ki * Ctprime * (1.0_R8Ki - an)**2 * &
               sin_eff_yaw * cos_eff_yaw2
      residuals(3) = v4_new - v4

      !------------------------------------------------------------------------
      ! Eq. 4: Near-wake length (Liew et al. 2024)
      ! x0 = cos(yaw)/(2*beta) * (1+u4)/|1-u4| * sqrt((1-an)*cos(yaw)/(1+u4))
      ! x0 is non-dimensionalized by D
      !------------------------------------------------------------------------
      if (abs(1.0_R8Ki - u4) > 1.0e-10_R8Ki .and. (1.0_R8Ki + u4) > 1.0e-10_R8Ki .and. &
         (1.0_R8Ki - an) * cos_eff_yaw / (1.0_R8Ki + u4) >= 0.0_R8Ki) then
         
         x0_new = cos_eff_yaw / &
                  (2.0_R8Ki * UMM_BETA) * &
                  (1.0_R8Ki + u4) / &
                  abs(1.0_R8Ki - u4) * &
                  sqrt((1.0_R8Ki - an) * cos_eff_yaw / (1.0_R8Ki + u4))
      else
         x0_new = x0_val  ! Error handling: keep current value if division or sqrt would fail
      endif
      residuals(4) = x0_new - x0_val

      !------------------------------------------------------------------------
      ! Eq. 5: Outlet pressure drop (Liew et al. 2024)
      ! dp = p_linear + p_g
      ! where p_linear = -(1/(2*pi)) * Ctprime * (1-an)^2 * cos^2(yaw) * atan(1/(2*x0))
      !------------------------------------------------------------------------
      p_linear = -(1.0_R8Ki / (2.0_R8Ki * pi_D)) * Ctprime * (1.0_R8Ki - an)**2 * &
                 cos_eff_yaw2 * atan(1.0_R8Ki / (2.0_R8Ki * max(x0_val, 0.01_R8Ki)))
      dp_new = p_linear + p_g
      residuals(5) = dp_new - dp

      !------------------------------------------------------------------------
      ! Eq. 6: CT-Ctprime relationship (Liew et al. 2024)
      ! Ctprime = CT / ((1-an)^2 * cos^2(yaw))
      !------------------------------------------------------------------------
      if (abs(1.0_R8Ki - an) > 1.0e-10_R8Ki) then
         Ctprime_new = CT_used / ((1.0_R8Ki - an)**2 * cos_eff_yaw2)
      else
         Ctprime_new = Ctprime  ! Error handling: keep current value to avoid division by zero
      endif
      residuals(6) = Ctprime_new - Ctprime

   end subroutine computeUMMResiduals6

   !> Get initial guess for UMM state vector
   !! Ref: MITRotor git repo (Howland-Lab/Unified-Momentum-Model)
   subroutine getUMMInitialGuess(CT, k, F, eff_yaw, x0_state)
      implicit none
      real(R8Ki), intent(in)  :: CT          !< Thrust coefficient from velocity-based formulation
      real(R8Ki), intent(in)  :: k           !< Thrust parameter from BEM (for logging only)
      real(ReKi), intent(in)  :: F           !< Tip/hub loss factor
      real(R8Ki), intent(in)  :: eff_yaw     !< Effective yaw angle [rad]
      real(R8Ki), intent(out) :: x0_state(6) !< Initial state vector: (an, u4, v4, x0, dp, Ctprime)

      real(R8Ki) :: CT_used, an_init, Ctprime_init
      real(R8Ki) :: cos_eff_yaw2

      cos_eff_yaw2 = cos(eff_yaw)**2

      ! Floor cos^2(yaw) to prevent division by zero
      if (cos_eff_yaw2 < 1.0e-10_R8Ki) then
         cos_eff_yaw2 = 1.0e-10_R8Ki
      endif

      CT_used = CT
      CT_used = max(-4.0_R8Ki, min(CT_used, 10.0_R8Ki))

      ! Initial guess for axial induction
      an_init = 0.5_R8Ki * CT_used
      an_init = max(0.0_R8Ki, min(an_init, 0.9_R8Ki))  ! Bound to reasonable range

      ! Initial Ctprime estimate (sign only, to avoid extreme values at high yaw)
      Ctprime_init = sign(1.0_R8Ki, CT_used)

      ! x = (an, u4, v4, x0, dp, Ctprime)
      x0_state(1) = an_init                  ! Axial induction
      x0_state(2) = 1.0_R8Ki - CT_used       ! Streamwise outlet velocity
      x0_state(3) = 0.0_R8Ki                 ! Lateral outlet velocity (zero initially)
      x0_state(4) = 100.0_R8Ki               ! Near-wake length (default)
      x0_state(5) = 0.0_R8Ki                 ! Pressure drop (zero initially)
      x0_state(6) = Ctprime_init             ! Initial Ctprime estimate

   end subroutine getUMMInitialGuess

end module UMM_FixedPointIteration
