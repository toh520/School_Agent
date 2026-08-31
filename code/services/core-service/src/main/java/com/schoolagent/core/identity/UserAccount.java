package com.schoolagent.core.identity;

import java.time.Instant;
import java.util.UUID;

public record UserAccount(
    UUID id,
    String username,
    String passwordHash,
    String studentNumber,
    String realName,
    String phone,
    UserRole role,
    String status,
    String nickname,
    String avatarUrl,
    String contact,
    Instant createdAt,
    Instant updatedAt) {

  public boolean active() {
    return "ACTIVE".equals(status);
  }
}
