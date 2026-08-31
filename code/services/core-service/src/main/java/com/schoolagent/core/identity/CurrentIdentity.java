package com.schoolagent.core.identity;

import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;

/** Authenticated identity derived exclusively from the verified JWT, never request parameters. */
public record CurrentIdentity(UUID userId, UUID sessionId, UserRole role) {

  public static CurrentIdentity from(Authentication authentication) {
    if (!(authentication instanceof JwtAuthenticationToken token)) {
      throw new BusinessException(ErrorCode.UNAUTHENTICATED, HttpStatus.UNAUTHORIZED);
    }
    try {
      return new CurrentIdentity(
          UUID.fromString(token.getToken().getSubject()),
          UUID.fromString(token.getToken().getClaimAsString("sid")),
          UserRole.valueOf(token.getToken().getClaimAsString("role")));
    } catch (IllegalArgumentException exception) {
      throw new BusinessException(ErrorCode.UNAUTHENTICATED, HttpStatus.UNAUTHORIZED);
    }
  }
}
