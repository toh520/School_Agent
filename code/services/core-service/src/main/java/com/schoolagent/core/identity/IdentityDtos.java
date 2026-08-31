package com.schoolagent.core.identity;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Public M02 request and response schemas kept together as one API contract. */
public final class IdentityDtos {

  private IdentityDtos() {}

  public record LoginRequest(
      @NotBlank @Size(max = 64) String username, @NotBlank @Size(max = 128) String password) {}

  public record RegisterRequest(
      @NotBlank @Pattern(regexp = "[0-9]{6,20}") String studentNumber,
      @NotBlank @Pattern(regexp = "1[3-9][0-9]{9}") String phone,
      @NotBlank @Size(min = 2, max = 50) String realName,
      @NotBlank @Pattern(regexp = "[A-Za-z0-9_]{4,32}") String username,
      @NotBlank @Size(min = 8, max = 72) String password,
      @NotBlank @Size(min = 8, max = 72) String confirmPassword) {}

  public record RefreshRequest(@NotBlank @Size(max = 500) String refreshToken) {}

  public record TokenResponse(
      String accessToken,
      String refreshToken,
      String tokenType,
      long expiresIn,
      UserSummary user) {}

  public record UserSummary(UUID id, String username, UserRole role, String nickname) {}

  public record ProfileResponse(
      UUID id,
      String username,
      String studentNumber,
      String realName,
      String phone,
      UserRole role,
      String nickname,
      String avatarUrl,
      String contact,
      Instant updatedAt) {}

  public record ProfileUpdateRequest(
      @NotBlank @Size(max = 80) String nickname,
      @Size(max = 500) String avatarUrl,
      @Size(max = 120) String contact) {}

  public record PreferenceResponse(
      List<String> tastes,
      BigDecimal budget,
      List<String> avoidances,
      List<String> allergens,
      String dietaryGoal,
      Instant updatedAt) {}

  public record PreferenceUpdateRequest(
      @Size(max = 20) List<@NotBlank @Size(max = 40) String> tastes,
      @DecimalMin("0.00") BigDecimal budget,
      @Size(max = 20) List<@NotBlank @Size(max = 40) String> avoidances,
      @Size(max = 20) List<@NotBlank @Size(max = 60) String> allergens,
      @Size(max = 200) String dietaryGoal) {}

  public record AuthorizationUpdateRequest(boolean granted) {}

  public record AuthorizationResponse(DataScope scope, boolean granted, Instant changedAt) {}

  public record MeResponse(
      ProfileResponse profile,
      PreferenceResponse preference,
      Map<DataScope, AuthorizationResponse> authorizations) {}

  public record CleanupRequest(@NotEmpty Set<DataScope> scopes) {}

  public record CleanupResult(
      UUID recordId, DataScope scope, int deletedRecords, Instant completedAt) {}

  public record AuditEventResponse(
      long id,
      UUID userId,
      UUID actorUserId,
      String eventType,
      String module,
      String targetType,
      String targetId,
      String outcome,
      String requestId,
      Instant occurredAt) {}
}
