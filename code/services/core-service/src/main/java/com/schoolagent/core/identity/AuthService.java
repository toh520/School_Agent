package com.schoolagent.core.identity;

import com.schoolagent.core.identity.AuthSessionRepository.SessionRecord;
import com.schoolagent.core.identity.IdentityDtos.LoginRequest;
import com.schoolagent.core.identity.IdentityDtos.RegisterRequest;
import com.schoolagent.core.identity.IdentityDtos.TokenResponse;
import com.schoolagent.core.identity.IdentityDtos.UserSummary;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.time.Instant;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Implements password login, refresh rotation and immediate server-side logout. */
@Service
public class AuthService {

  private final UserRepository users;
  private final RegistrationService registration;
  private final AuthSessionRepository sessions;
  private final AuditService audits;
  private final TokenService tokenService;
  private final PasswordEncoder passwordEncoder;
  private final String dummyPasswordHash;

  public AuthService(
      UserRepository users,
      RegistrationService registration,
      AuthSessionRepository sessions,
      AuditService audits,
      TokenService tokenService,
      PasswordEncoder passwordEncoder) {
    this.users = users;
    this.registration = registration;
    this.sessions = sessions;
    this.audits = audits;
    this.tokenService = tokenService;
    this.passwordEncoder = passwordEncoder;
    this.dummyPasswordHash = passwordEncoder.encode("timing-only-dummy-password");
  }

  public TokenResponse register(RegisterRequest request, String requestId) {
    UserAccount user = registration.create(request);
    TokenResponse response = createSession(user, "REGISTER_SUCCESS", requestId);
    return response;
  }

  @Transactional
  public TokenResponse login(LoginRequest request, String requestId) {
    UserAccount user = users.findByUsername(request.username()).orElse(null);
    String candidateHash = user == null ? dummyPasswordHash : user.passwordHash();
    if (!passwordEncoder.matches(request.password(), candidateHash) || user == null) {
      audits.record(
          user == null ? null : user.id(),
          user == null ? null : user.id(),
          "LOGIN_FAILED",
          "IAM",
          "USER",
          user == null ? null : user.id().toString(),
          "FAILED",
          requestId);
      throw new BusinessException(ErrorCode.INVALID_CREDENTIALS, HttpStatus.UNAUTHORIZED);
    }
    if (!user.active()) {
      audits.record(
          user.id(),
          user.id(),
          "LOGIN_DISABLED",
          "IAM",
          "USER",
          user.id().toString(),
          "DENIED",
          requestId);
      throw new BusinessException(ErrorCode.ACCOUNT_DISABLED, HttpStatus.FORBIDDEN);
    }

    return createSession(user, "LOGIN_SUCCESS", requestId);
  }

  @Transactional
  public TokenResponse refresh(String refreshToken, String requestId) {
    SessionRecord session =
        sessions
            .findActiveByRefreshHash(tokenService.hashRefreshToken(refreshToken))
            .orElseThrow(
                () -> new BusinessException(ErrorCode.UNAUTHENTICATED, HttpStatus.UNAUTHORIZED));
    UserAccount user =
        users
            .findById(session.userId())
            .filter(UserAccount::active)
            .orElseThrow(
                () -> new BusinessException(ErrorCode.UNAUTHENTICATED, HttpStatus.UNAUTHORIZED));
    String newRefreshToken = tokenService.newRefreshToken();
    sessions.rotate(
        session.id(), tokenService.hashRefreshToken(newRefreshToken), tokenService.refreshExpiry());
    audits.record(
        user.id(),
        user.id(),
        "TOKEN_REFRESHED",
        "IAM",
        "SESSION",
        session.id().toString(),
        "SUCCESS",
        requestId);
    return response(user, session.id(), newRefreshToken);
  }

  @Transactional
  public void logout(CurrentIdentity identity, String requestId) {
    sessions.revoke(identity.sessionId(), identity.userId());
    audits.record(
        identity.userId(),
        identity.userId(),
        "LOGOUT",
        "IAM",
        "SESSION",
        identity.sessionId().toString(),
        "SUCCESS",
        requestId);
  }

  private TokenResponse response(UserAccount user, UUID sessionId, String refreshToken) {
    TokenService.AccessToken accessToken = tokenService.accessToken(user, sessionId);
    return new TokenResponse(
        accessToken.value(),
        refreshToken,
        "Bearer",
        accessToken.expiresIn(),
        new UserSummary(user.id(), user.username(), user.role(), user.nickname()));
  }

  private TokenResponse createSession(UserAccount user, String eventType, String requestId) {
    String refreshToken = tokenService.newRefreshToken();
    Instant refreshExpiry = tokenService.refreshExpiry();
    UUID sessionId =
        sessions.create(user.id(), tokenService.hashRefreshToken(refreshToken), refreshExpiry);
    audits.record(
        user.id(),
        user.id(),
        eventType,
        "IAM",
        "SESSION",
        sessionId.toString(),
        "SUCCESS",
        requestId);
    return response(user, sessionId, refreshToken);
  }
}
