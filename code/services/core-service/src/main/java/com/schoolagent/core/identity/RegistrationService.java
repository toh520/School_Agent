package com.schoolagent.core.identity;

import com.schoolagent.core.identity.IdentityDtos.RegisterRequest;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Creates student accounts and their default-deny personal-data state atomically. */
@Service
public class RegistrationService {

  private final UserRepository users;
  private final UserDataRepository userData;
  private final PasswordEncoder passwordEncoder;

  public RegistrationService(
      UserRepository users, UserDataRepository userData, PasswordEncoder passwordEncoder) {
    this.users = users;
    this.userData = userData;
    this.passwordEncoder = passwordEncoder;
  }

  @Transactional
  public UserAccount create(RegisterRequest request) {
    if (!request.password().equals(request.confirmPassword())) {
      throw conflict(ErrorCode.PASSWORD_MISMATCH);
    }
    if (users.existsByUsername(request.username())) {
      throw conflict(ErrorCode.USERNAME_ALREADY_EXISTS);
    }
    if (users.existsByStudentNumber(request.studentNumber())) {
      throw conflict(ErrorCode.STUDENT_NUMBER_ALREADY_EXISTS);
    }
    if (users.existsByPhone(request.phone())) {
      throw conflict(ErrorCode.PHONE_ALREADY_EXISTS);
    }
    try {
      UserAccount user =
          users.createStudent(
              request.username(),
              passwordEncoder.encode(request.password()),
              request.studentNumber(),
              request.realName(),
              request.phone());
      userData.initialize(user.id());
      return user;
    } catch (DuplicateKeyException exception) {
      // Database constraints remain authoritative when concurrent requests race.
      throw conflict(ErrorCode.CONFLICT);
    }
  }

  private BusinessException conflict(ErrorCode errorCode) {
    return new BusinessException(errorCode, HttpStatus.CONFLICT);
  }
}
