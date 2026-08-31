package com.schoolagent.core.identity;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.schoolagent.core.identity.IdentityDtos.RegisterRequest;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class RegistrationServiceTest {

  @Mock private UserRepository users;
  @Mock private UserDataRepository userData;
  @Mock private PasswordEncoder passwordEncoder;

  private RegistrationService service;

  @BeforeEach
  void setUp() {
    service = new RegistrationService(users, userData, passwordEncoder);
  }

  @Test
  void createsStudentAndDefaultPersonalDataState() {
    RegisterRequest request = request("new_student", "13900000003", "password123");
    UserAccount user = user(request);
    when(passwordEncoder.encode("password123")).thenReturn("hash");
    when(users.createStudent(
            request.username(),
            "hash",
            request.studentNumber(),
            request.realName(),
            request.phone()))
        .thenReturn(user);

    service.create(request);

    verify(userData).initialize(user.id());
  }

  @Test
  void rejectsMismatchedPasswordsBeforeWriting() {
    RegisterRequest request = request("new_student", "13900000003", "different-password");

    assertThatThrownBy(() -> service.create(request))
        .isInstanceOfSatisfying(
            BusinessException.class,
            exception ->
                org.assertj.core.api.Assertions.assertThat(exception.getErrorCode())
                    .isEqualTo(ErrorCode.PASSWORD_MISMATCH));
    verifyNoInteractions(users, userData);
  }

  @Test
  void rejectsDuplicateStudentNumberWithStableCode() {
    RegisterRequest request = request("new_student", "13900000003", "password123");
    when(users.existsByStudentNumber(request.studentNumber())).thenReturn(true);

    assertThatThrownBy(() -> service.create(request))
        .isInstanceOfSatisfying(
            BusinessException.class,
            exception ->
                org.assertj.core.api.Assertions.assertThat(exception.getErrorCode())
                    .isEqualTo(ErrorCode.STUDENT_NUMBER_ALREADY_EXISTS));
  }

  private RegisterRequest request(String username, String phone, String confirmation) {
    return new RegisterRequest("2026000003", phone, "新学生", username, "password123", confirmation);
  }

  private UserAccount user(RegisterRequest request) {
    return new UserAccount(
        UUID.randomUUID(),
        request.username(),
        "hash",
        request.studentNumber(),
        request.realName(),
        request.phone(),
        UserRole.STUDENT,
        "ACTIVE",
        request.realName(),
        null,
        null,
        Instant.now(),
        Instant.now());
  }
}
