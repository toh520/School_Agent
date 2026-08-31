package com.schoolagent.core.identity;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.IdentityDtos.LoginRequest;
import com.schoolagent.core.identity.IdentityDtos.RefreshRequest;
import com.schoolagent.core.identity.IdentityDtos.RegisterRequest;
import com.schoolagent.core.identity.IdentityDtos.TokenResponse;
import com.schoolagent.core.web.ApiResponse;
import jakarta.validation.Valid;
import org.slf4j.MDC;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

  private final AuthService authService;

  public AuthController(AuthService authService) {
    this.authService = authService;
  }

  @PostMapping("/login")
  public ApiResponse<TokenResponse> login(@Valid @RequestBody LoginRequest request) {
    return ApiResponse.success(authService.login(request, requestId()), requestId());
  }

  @PostMapping("/register")
  public ApiResponse<TokenResponse> register(@Valid @RequestBody RegisterRequest request) {
    return ApiResponse.success(authService.register(request, requestId()), requestId());
  }

  @PostMapping("/refresh")
  public ApiResponse<TokenResponse> refresh(@Valid @RequestBody RefreshRequest request) {
    return ApiResponse.success(
        authService.refresh(request.refreshToken(), requestId()), requestId());
  }

  @PostMapping("/logout")
  public ApiResponse<Void> logout(Authentication authentication) {
    authService.logout(CurrentIdentity.from(authentication), requestId());
    return ApiResponse.success(null, requestId());
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
