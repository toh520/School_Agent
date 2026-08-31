package com.schoolagent.core.identity;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.schoolagent.core.identity.IdentityDtos.AuthorizationResponse;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

  @Mock private UserRepository users;
  @Mock private UserDataRepository userData;
  @Mock private AuditService audits;

  private UserService service;

  @BeforeEach
  void setUp() {
    service = new UserService(users, userData, audits);
  }

  @Test
  void deniesStudentReadingAnotherUsersProfileAndAuditsAttempt() {
    UUID actor = UUID.randomUUID();
    UUID target = UUID.randomUUID();
    CurrentIdentity identity = new CurrentIdentity(actor, UUID.randomUUID(), UserRole.STUDENT);

    assertThatThrownBy(() -> service.profileById(identity, target, "request-denied"))
        .isInstanceOfSatisfying(
            BusinessException.class,
            exception -> assertThat(exception.getErrorCode()).isEqualTo(ErrorCode.FORBIDDEN));
    verify(audits)
        .record(
            target,
            actor,
            "RESOURCE_ACCESS",
            "IAM",
            "USER_PROFILE",
            target.toString(),
            "DENIED",
            "request-denied");
  }

  @Test
  void revokingAuthorizationAlsoCleansScopedMemory() {
    UUID userId = UUID.randomUUID();
    CurrentIdentity identity = new CurrentIdentity(userId, UUID.randomUUID(), UserRole.STUDENT);
    AuthorizationResponse revoked = new AuthorizationResponse(DataScope.DIET, false, Instant.now());
    when(userData.updateAuthorization(userId, DataScope.DIET, false)).thenReturn(revoked);

    AuthorizationResponse result =
        service.updateAuthorization(identity, DataScope.DIET, false, "request-revoke");

    assertThat(result.granted()).isFalse();
    verify(userData).cleanup(userId, DataScope.DIET, "AUTHORIZATION_REVOKED");
  }
}
