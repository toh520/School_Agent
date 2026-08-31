package com.schoolagent.core.identity;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.schoolagent.core.identity.IdentityDtos.LoginRequest;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

  @Mock private UserRepository users;
  @Mock private RegistrationService registration;
  @Mock private AuthSessionRepository sessions;
  @Mock private AuditService audits;
  @Mock private TokenService tokens;
  @Mock private PasswordEncoder passwordEncoder;

  private AuthService service;

  @BeforeEach
  void setUp() {
    when(passwordEncoder.encode(any())).thenReturn("dummy-hash");
    service = new AuthService(users, registration, sessions, audits, tokens, passwordEncoder);
  }

  @Test
  void logsInActiveUserAndCreatesRevocableSession() {
    UserAccount user = user("ACTIVE");
    UUID sessionId = UUID.randomUUID();
    when(users.findByUsername("student1")).thenReturn(Optional.of(user));
    when(passwordEncoder.matches("Student@123", "hash")).thenReturn(true);
    when(tokens.newRefreshToken()).thenReturn("refresh-token");
    when(tokens.hashRefreshToken("refresh-token")).thenReturn("refresh-hash");
    when(tokens.refreshExpiry()).thenReturn(Instant.now().plusSeconds(3600));
    when(sessions.create(any(), any(), any())).thenReturn(sessionId);
    when(tokens.accessToken(user, sessionId))
        .thenReturn(new TokenService.AccessToken("access-token", 900));

    var response = service.login(new LoginRequest("student1", "Student@123"), "request-1");

    assertThat(response.accessToken()).isEqualTo("access-token");
    assertThat(response.refreshToken()).isEqualTo("refresh-token");
    verify(sessions).create(user.id(), "refresh-hash", tokens.refreshExpiry());
  }

  @Test
  void rejectsInvalidPasswordWithStableCode() {
    UserAccount user = user("ACTIVE");
    when(users.findByUsername("student1")).thenReturn(Optional.of(user));
    when(passwordEncoder.matches("wrong", "hash")).thenReturn(false);

    assertThatThrownBy(() -> service.login(new LoginRequest("student1", "wrong"), "request-2"))
        .isInstanceOfSatisfying(
            BusinessException.class,
            exception ->
                assertThat(exception.getErrorCode()).isEqualTo(ErrorCode.INVALID_CREDENTIALS));
  }

  @Test
  void rejectsDisabledAccountAfterPasswordVerification() {
    UserAccount user = user("DISABLED");
    when(users.findByUsername("student1")).thenReturn(Optional.of(user));
    when(passwordEncoder.matches("Student@123", "hash")).thenReturn(true);

    assertThatThrownBy(
            () -> service.login(new LoginRequest("student1", "Student@123"), "request-3"))
        .isInstanceOfSatisfying(
            BusinessException.class,
            exception ->
                assertThat(exception.getErrorCode()).isEqualTo(ErrorCode.ACCOUNT_DISABLED));
  }

  private UserAccount user(String status) {
    return new UserAccount(
        UUID.randomUUID(),
        "student1",
        "hash",
        "2026000001",
        "学生用户一",
        "13900000001",
        UserRole.STUDENT,
        status,
        "学生",
        null,
        null,
        Instant.now(),
        Instant.now());
  }
}
