!**********************************************************************************************************************************
! UMM_FixedPointIteration Module
! Unified Momentum Model (UMM) Module for OpenFAST Implementation
!
! This module contains:
!   - UMM iteration parameters (BETA, V4_CORR, MAX_ITER, TOLERANCE, RELAXATION)
!   - computeUMMResiduals6: Compute the 6 UMM residual equations
!   - getUMMInitialGuess: Get initial guess for UMM iteration (using LimitedHeck from https://github.com/Howland-Lab/Unified-Momentum-Model/blob/main/UnifiedMomentumModel/Momentum.py)
!
! Reference Paper: Liew et al. 2024 - https://www.nature.com/articles/s41467-024-50756-5
! Code Source (Python): https://github.com/Howland-Lab/Unified-Momentum-Model/blob/main/UnifiedMomentumModel/Momentum.py
!
!**********************************************************************************************************************************
module UMM_FixedPointIteration

   use NWTC_Library
   use UMM_Pressure

   implicit none

   private

   !-------------------------------------------------------------------------------------------------
   ! UMM Iteration Parameters
   ! From Python ThrustBasedUnified class (lines 329-330)
   !-------------------------------------------------------------------------------------------------
   integer(IntKi), public, parameter :: UMM_MAX_ITER = 10000         ! Maximum iterations (ThrustBasedUnified uses 10k)
   real(R8Ki),     public, parameter :: UMM_TOLERANCE = 1.0e-5_R8Ki  ! Convergence tolerance on residuals
   real(R8Ki),     public, parameter :: UMM_RELAXATION = 0.4_R8Ki    ! Relaxation factor (ThrustBasedUnified: [0.4, 0.6])

   ! NOTE: OpenFAST has existing parameters that could be reused, but the appropriate tol and max_iter may vary:
   !   p%aTol             - tolerance for induction solve (typically 5e-5 to 5e-10)
   !   p%maxIndIterations - maximum iterations (from input file)
   ! Hardcoding UMM iteration settings for now (TODO)

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

   !> Compute the 6 UMM residual equations (ThrustBasedUnified model)
   !! x = (an, u4, v4, x0, dp, Ctprime)
   !!
   !! The 6 equations are:
   !!   Eq 1: Rotor-normal induction (Eq. 1 in Liew et al 2024)
   !!   Eq 2: Streamwise outlet velocity (Eq. 2 in Liew et al 2024)
   !!   Eq 3: Lateral outlet velocity (Eq. 3 in Liew 2et al 024)
   !!   Eq 4: Near-wake length (Eq. 4 in Liew et al 2024)
   !!   Eq 5: Outlet pressure drop (Eq. 5 in Liew et al 2024)
   !!   Eq 6: CT-Ctprime relationship (Eq. 6 in Liew et al 2024)
   !!
   !! @param x = (an, u4, v4, x0, dp, Ctprime)
   !! @param CT Thrust coefficient computed directly from blade element (matches MITRotor formulation)
   !! @param k Thrust parameter from BEM (kept for comparison logging only)
   !! @param F Tip/hub loss factor
   !! @param eff_yaw Effective yaw angle [rad]
   !! @param residuals Output residuals
   subroutine computeUMMResiduals6(x, CT, k, F, eff_yaw, residuals)
      implicit none
      real(R8Ki), intent(in)  :: x(6)         !< x = (an, u4, v4, x0, dp, Ctprime)
      real(R8Ki), intent(in)  :: CT           !< Thrust coefficient (direct from blade element, no sin^2(phi) singularity)
      real(R8Ki), intent(in)  :: k            !< Thrust parameter from BEM (for comparison logging only)
      real(ReKi), intent(in)  :: F            !< Tip/hub loss factor
      real(R8Ki), intent(in)  :: eff_yaw      !< Effective yaw angle [rad]
      real(R8Ki), intent(out) :: residuals(6) !< Output residuals

      ! Local variables (x) to solve via fixed point iteration
      real(R8Ki) :: an, u4, v4, x0_val, dp, Ctprime
      ! Intermediate calculations for system of equations (Liew et al 2024 Eq. 1 - 6)
      real(R8Ki) :: cos_eff_yaw, cos_eff_yaw2, sin_eff_yaw
      real(R8Ki) :: CT_used, CT_old, dp_half, p_g, p_linear
      real(R8Ki) :: term1, term2_sqrt_arg, sqrt_arg1
      real(R8Ki) :: an_new, u4_new, v4_new, x0_new, dp_new, Ctprime_new

      ! Extract state variables (x)
      an      = x(1)
      u4      = x(2)    ! non-dimensionalized as fraction of u_inf
      v4      = x(3)    ! non-dimensionalized as fraction of u_inf
      x0_val  = x(4)
      dp      = x(5)
      Ctprime = x(6)

      ! Precompute trigonometric terms w.r.t. skewed inflow
      cos_eff_yaw  = cos(eff_yaw)
      cos_eff_yaw2 = cos_eff_yaw**2
      sin_eff_yaw  = sin(eff_yaw)

      ! Avoid cos2(yaw) = 0 to prevent numerical instability in Eq. 1
      if (cos_eff_yaw2 < 1.0e-10_R8Ki) then
         cos_eff_yaw2 = 1.0e-10_R8Ki
      endif

      ! Handle CT=0 scenario and avoid numerical instability in Eq. 1
      if (abs(Ctprime) < 1.0e-10_R8Ki) then
         residuals(1) = -an                  ! an = an - an = 0
         residuals(2) = 1.0_R8Ki - u4        ! u4 = u4 + (1 - u4) = 1
         residuals(3) = -v4                  ! v4 = v4 - v4 = 0
         residuals(4) = 100.0_R8Ki - x0_val  ! x0_val = x0_val + (100 - x0_val) = 100
         residuals(5) = -dp                  ! dp = dp - dp = 0
         residuals(6) = -Ctprime             ! Ctprime = Ctprime - Ctprime = 0
         return
      endif

      ! CT calculated from velocity-based formulation to avoid numerical instabilty observed in k-based approach when phi is small
      CT_used = CT

      ! Clamp CT to physically reasonable bounds
      CT_used = max(-4.0_R8Ki, min(CT_used, 10.0_R8Ki))

      !------------------------------------------------------------------------
      ! OLD: Compute CT from k and current an
      ! This approach had a singularity when phi -> 0 because k = sigma*Cn/(4F*sin^2(phi))
      ! CT = 4*F*k*(1-an)^2
      ! CT_old = 4.0_R8Ki * real(F, R8Ki) * k * (1.0_R8Ki - an)**2
      ! CT_old = max(-4.0_R8Ki, min(CT_old, 10.0_R8Ki))
      !------------------------------------------------------------------------

      ! Get nonlinear pressure correction from table
      ! dp = CT/2 = Δp / (rho * u_inf^2) derived from AD theory:
      !
      ! CT = |F_t| / (0.5 * rho * u_inf^2 * A)
      ! F_t = dp * A
      !
      dp_half = CT_used / 2.0_R8Ki

      ! Call bilinear interpoltation of pre-cached nonlinear pressure table at dp and x0 indices
      p_g = interpolatePressureTable(dp_half, max(x0_val, 0.01_R8Ki))

      !------------------------------------------------------------------------
      ! Equation 1: Rotor-normal induction (Eq. 1 in Liew et al 2024)
      ! an = 1 - sqrt(-dp/(0.5*Ctprime*cos^2(yaw)) + (1-u4^2-v4^2)/(Ctprime*cos^2(yaw)))
      !
      ! NOTE: velocities are non-dimensionalized by normalizing by u_inf 
      ! (u_inf is non-dimensionalized to 1 via normalization and therefore vanishes from several terms in the equations below)
      !
      ! NOTE: density is already encoded in the denominator of dp = Δp / (ρ * u∞²)
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
      ! Equation 2: Streamwise outlet velocity (Eq. 2 in Liew et al 2024)
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
      ! Equation 3: Lateral outlet velocity (Eq. 3 in Liew et al 2024)
      ! v4 = -v4_corr * 0.25 * Ctprime * (1-an)^2 * sin(yaw) * cos^2(yaw)
      !------------------------------------------------------------------------
      v4_new = -UMM_V4_CORR * 0.25_R8Ki * Ctprime * (1.0_R8Ki - an)**2 * &
               sin_eff_yaw * cos_eff_yaw2
      residuals(3) = v4_new - v4

      !------------------------------------------------------------------------
      ! Equation 4: Near-wake length (Eq. 4 in Liew et al 2024)
      ! x0 = cos(yaw)/(2*beta) * (1+u4)/|1-u4| * sqrt((1-an)*cos(yaw)/(1+u4))
      !
      ! NOTE: x0_val is non-dimensionalized by D, thus D is not included in Eq. 4 and 5
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
      ! Equation 5: Outlet pressure drop (Eq. 5 in Liew et al 2024)
      ! dp = p_linear + p_g
      ! where p_linear = -(1/(2*pi)) * Ctprime * (1-an)^2 * cos^2(yaw) * atan(1/(2*x0))
      !------------------------------------------------------------------------
      p_linear = -(1.0_R8Ki / (2.0_R8Ki * pi_D)) * Ctprime * (1.0_R8Ki - an)**2 * &
                 cos_eff_yaw2 * atan(1.0_R8Ki / (2.0_R8Ki * max(x0_val, 0.01_R8Ki)))
      dp_new = p_linear + p_g
      residuals(5) = dp_new - dp

      !------------------------------------------------------------------------
      ! Equation 6: CT-Ctprime relationship (Eq. 6 in Liew et al 2024)
      ! Ctprime = CT / ((1-an)^2 * cos^2(yaw))
      !
      ! NEW: CT is now the direct input (computed from blade element velocity formulation)
      ! OLD: CT was computed from k as CT = 4*F*k*(1-an)^2, which had sin^2(phi) singularity
      !------------------------------------------------------------------------
      if (abs(1.0_R8Ki - an) > 1.0e-10_R8Ki) then
         Ctprime_new = CT_used / ((1.0_R8Ki - an)**2 * cos_eff_yaw2)
      else
         Ctprime_new = Ctprime  ! Error handling: keep current value to avoid division by zero
      endif
      residuals(6) = Ctprime_new - Ctprime

   end subroutine computeUMMResiduals6

   !> Get initial guess for UMM iteration using ThrustBasedUnified approach
   !! Reference: https://github.com/Howland-Lab/Unified-Momentum-Model/blob/main/UnifiedMomentumModel/Momentum.py, ThrustBasedUnified.initial_guess
   !!
   !! @param CT Thrust coefficient computed directly from blade element
   !! @param k Thrust parameter from BEM (kept for comparison logging only)
   !! @param F Tip/hub loss factor
   !! @param eff_yaw Effective yaw angle [rad]
   !! @param x0_state Output initial state vector: (an, u4, v4, x0, dp, Ctprime)
   subroutine getUMMInitialGuess(CT, k, F, eff_yaw, x0_state)
      implicit none
      real(R8Ki), intent(in)  :: CT          !< Thrust coefficient (direct from blade element, no sin^2(phi) singularity)
      real(R8Ki), intent(in)  :: k           !< Thrust parameter from BEM (for comparison logging only)
      real(ReKi), intent(in)  :: F           !< Tip/hub loss factor
      real(R8Ki), intent(in)  :: eff_yaw     !< Effective yaw angle [rad]
      real(R8Ki), intent(out) :: x0_state(6) !< Initial state vector: (an, u4, v4, x0, dp, Ctprime)

      real(R8Ki) :: CT_used, an_init, Ctprime_init
      real(R8Ki) :: cos_eff_yaw2

      cos_eff_yaw2 = cos(eff_yaw)**2

      ! Avoid cos2(yaw) = 0 to prevent numerical instability in Eq. 1
      if (cos_eff_yaw2 < 1.0e-10_R8Ki) then
         cos_eff_yaw2 = 1.0e-10_R8Ki
      endif

      ! CT calculated from velocity-based formulation to avoid numerical instabilty observed in k-based approach when phi is small
      CT_used = CT

      ! Clamp CT to physically reasonable bounds
      CT_used = max(-4.0_R8Ki, min(CT_used, 10.0_R8Ki))

      !------------------------------------------------------------------------
      ! OLD (COMMENTED OUT): Initial CT estimate assuming an ≈ 1/3
      ! CT = 4*F*k*(1-an)^2 ≈ 4*F*k*(2/3)^2 = 4*F*k*(4/9) from OpenFAST BEM solution
      ! This had the sin^2(phi) singularity embedded in k
      !
      ! if (abs(k) < 1.0e-10_R8Ki) then
      !    CT_init = 0.0_R8Ki
      ! else
      !    CT_init = 4.0_R8Ki * real(F, R8Ki) * k * (1.0_R8Ki - 1.0_R8Ki/3.0_R8Ki)**2
      ! endif
      ! CT_init = max(-4.0_R8Ki, min(CT_init, 10.0_R8Ki))
      !------------------------------------------------------------------------

      ! Initial guess for axial induction
      an_init = 0.5_R8Ki * CT_used
      an_init = max(0.0_R8Ki, min(an_init, 0.9_R8Ki))  ! Bound to reasonable range

      ! Initial Ctprime estimate - use simple sign(CT) to match Howland Lab reference
      ! Previous approach: Ctprime_init = CT_used / ((1-an_init)^2 * cos^2(yaw))
      ! This caused extreme values at high yaw angles, pushing iteration into ill-conditioned regions
      Ctprime_init = sign(1.0_R8Ki, CT_used)

      ! x = (an, u4, v4, x0, dp, Ctprime)
      x0_state(1) = an_init                  ! Axial induction
      x0_state(2) = 1.0_R8Ki - CT_used       ! Streamwise outlet velocity
      x0_state(3) = 0.0_R8Ki                 ! Lateral outlet velocity (zero initially)
      x0_state(4) = 100.0_R8Ki               ! Near-wake length (Howland Lab uses 100, was 50)
      x0_state(5) = 0.0_R8Ki                 ! Pressure drop (zero initially)
      x0_state(6) = Ctprime_init             ! Initial Ctprime estimate

   end subroutine getUMMInitialGuess

end module UMM_FixedPointIteration
