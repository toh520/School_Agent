package com.schoolagent.core.identity;

import com.schoolagent.core.identity.IdentityDtos.AuthorizationResponse;
import com.schoolagent.core.identity.IdentityDtos.CleanupResult;
import com.schoolagent.core.identity.IdentityDtos.MeResponse;
import com.schoolagent.core.identity.IdentityDtos.PreferenceResponse;
import com.schoolagent.core.identity.IdentityDtos.PreferenceUpdateRequest;
import com.schoolagent.core.identity.IdentityDtos.ProfileResponse;
import com.schoolagent.core.identity.IdentityDtos.ProfileUpdateRequest;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Owns profile, preference, authorization and data-cleanup rules for M02. */
@Service
public class UserService {

  private final UserRepository users;
  private final UserDataRepository userData;
  private final AuditService audits;

  public UserService(UserRepository users, UserDataRepository userData, AuditService audits) {
    this.users = users;
    this.userData = userData;
    this.audits = audits;
  }

  public MeResponse me(CurrentIdentity identity) {
    UserAccount user = requireUser(identity.userId());
    return new MeResponse(
        profile(user), userData.preference(user.id()), userData.authorizations(user.id()));
  }

  @Transactional
  public ProfileResponse updateProfile(
      CurrentIdentity identity, ProfileUpdateRequest request, String requestId) {
    UserAccount updated =
        users.updateProfile(
            identity.userId(), request.nickname(), request.avatarUrl(), request.contact());
    audits.record(
        identity.userId(),
        identity.userId(),
        "PROFILE_UPDATED",
        "IAM",
        "USER",
        identity.userId().toString(),
        "SUCCESS",
        requestId);
    return profile(updated);
  }

  @Transactional
  public PreferenceResponse updatePreference(
      CurrentIdentity identity, PreferenceUpdateRequest request, String requestId) {
    PreferenceResponse updated = userData.updatePreference(identity.userId(), request);
    audits.record(
        identity.userId(),
        identity.userId(),
        "PREFERENCE_UPDATED",
        "IAM",
        "USER_PREFERENCE",
        identity.userId().toString(),
        "SUCCESS",
        requestId);
    return updated;
  }

  @Transactional
  public AuthorizationResponse updateAuthorization(
      CurrentIdentity identity, DataScope scope, boolean granted, String requestId) {
    AuthorizationResponse updated = userData.updateAuthorization(identity.userId(), scope, granted);
    if (!granted) {
      userData.cleanup(identity.userId(), scope, "AUTHORIZATION_REVOKED");
    }
    audits.record(
        identity.userId(),
        identity.userId(),
        granted ? "AUTHORIZATION_GRANTED" : "AUTHORIZATION_REVOKED",
        "IAM",
        "DATA_AUTHORIZATION",
        scope.name(),
        "SUCCESS",
        requestId);
    return updated;
  }

  @Transactional
  public List<CleanupResult> cleanup(
      CurrentIdentity identity, Iterable<DataScope> scopes, String requestId) {
    List<CleanupResult> results =
        java.util.stream.StreamSupport.stream(scopes.spliterator(), false)
            .map(scope -> userData.cleanup(identity.userId(), scope, "USER_REQUEST"))
            .toList();
    audits.record(
        identity.userId(),
        identity.userId(),
        "DATA_CLEANUP",
        "IAM",
        "LONG_TERM_MEMORY",
        null,
        "SUCCESS",
        requestId);
    return results;
  }

  public ProfileResponse profileById(
      CurrentIdentity identity, UUID requestedUserId, String requestId) {
    if (identity.role() == UserRole.STUDENT && !identity.userId().equals(requestedUserId)) {
      audits.record(
          requestedUserId,
          identity.userId(),
          "RESOURCE_ACCESS",
          "IAM",
          "USER_PROFILE",
          requestedUserId.toString(),
          "DENIED",
          requestId);
      throw new BusinessException(ErrorCode.FORBIDDEN, HttpStatus.FORBIDDEN);
    }
    UserAccount target = requireUser(requestedUserId);
    audits.record(
        requestedUserId,
        identity.userId(),
        "RESOURCE_ACCESS",
        "IAM",
        "USER_PROFILE",
        requestedUserId.toString(),
        "SUCCESS",
        requestId);
    return profile(target);
  }

  private UserAccount requireUser(UUID userId) {
    return users
        .findById(userId)
        .orElseThrow(
            () -> new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND));
  }

  private ProfileResponse profile(UserAccount user) {
    return new ProfileResponse(
        user.id(),
        user.username(),
        user.studentNumber(),
        user.realName(),
        user.phone(),
        user.role(),
        user.nickname(),
        user.avatarUrl(),
        user.contact(),
        user.updatedAt());
  }
}
