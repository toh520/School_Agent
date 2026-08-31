package com.schoolagent.core.identity;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.IdentityDtos.AuthorizationResponse;
import com.schoolagent.core.identity.IdentityDtos.AuthorizationUpdateRequest;
import com.schoolagent.core.identity.IdentityDtos.CleanupRequest;
import com.schoolagent.core.identity.IdentityDtos.CleanupResult;
import com.schoolagent.core.identity.IdentityDtos.MeResponse;
import com.schoolagent.core.identity.IdentityDtos.PreferenceResponse;
import com.schoolagent.core.identity.IdentityDtos.PreferenceUpdateRequest;
import com.schoolagent.core.identity.IdentityDtos.ProfileResponse;
import com.schoolagent.core.identity.IdentityDtos.ProfileUpdateRequest;
import com.schoolagent.core.web.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

  private final UserService userService;

  public UserController(UserService userService) {
    this.userService = userService;
  }

  @GetMapping("/me")
  public ApiResponse<MeResponse> me(Authentication authentication) {
    return ApiResponse.success(userService.me(CurrentIdentity.from(authentication)), requestId());
  }

  @PatchMapping("/me/profile")
  @PreAuthorize("hasRole('STUDENT')")
  public ApiResponse<ProfileResponse> updateProfile(
      Authentication authentication, @Valid @RequestBody ProfileUpdateRequest request) {
    return ApiResponse.success(
        userService.updateProfile(CurrentIdentity.from(authentication), request, requestId()),
        requestId());
  }

  @PutMapping("/me/preferences")
  @PreAuthorize("hasRole('STUDENT')")
  public ApiResponse<PreferenceResponse> updatePreference(
      Authentication authentication, @Valid @RequestBody PreferenceUpdateRequest request) {
    return ApiResponse.success(
        userService.updatePreference(CurrentIdentity.from(authentication), request, requestId()),
        requestId());
  }

  @PutMapping("/me/authorizations/{scope}")
  @PreAuthorize("hasRole('STUDENT')")
  public ApiResponse<AuthorizationResponse> updateAuthorization(
      Authentication authentication,
      @PathVariable DataScope scope,
      @RequestBody AuthorizationUpdateRequest request) {
    return ApiResponse.success(
        userService.updateAuthorization(
            CurrentIdentity.from(authentication), scope, request.granted(), requestId()),
        requestId());
  }

  @PostMapping("/me/data-cleanup")
  @PreAuthorize("hasRole('STUDENT')")
  public ApiResponse<List<CleanupResult>> cleanup(
      Authentication authentication, @Valid @RequestBody CleanupRequest request) {
    return ApiResponse.success(
        userService.cleanup(CurrentIdentity.from(authentication), request.scopes(), requestId()),
        requestId());
  }

  @GetMapping("/{userId}/profile")
  public ApiResponse<ProfileResponse> profileById(
      Authentication authentication, @PathVariable UUID userId) {
    return ApiResponse.success(
        userService.profileById(CurrentIdentity.from(authentication), userId, requestId()),
        requestId());
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
