package com.schoolagent.core.security;

import com.schoolagent.core.identity.AuthSessionRepository;
import com.schoolagent.core.web.ErrorCode;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** Enforces server-side session revocation in addition to JWT signature and expiry checks. */
@Component
public class SessionValidationFilter extends OncePerRequestFilter {

  private final AuthSessionRepository sessions;
  private final SecurityResponseWriter responseWriter;

  public SessionValidationFilter(
      AuthSessionRepository sessions, SecurityResponseWriter responseWriter) {
    this.sessions = sessions;
    this.responseWriter = responseWriter;
  }

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
      throws ServletException, IOException {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    if (authentication instanceof JwtAuthenticationToken token) {
      try {
        UUID userId = UUID.fromString(token.getToken().getSubject());
        UUID sessionId = UUID.fromString(token.getToken().getClaimAsString("sid"));
        if (!sessions.isActive(sessionId, userId)) {
          SecurityContextHolder.clearContext();
          responseWriter.write(response, 401, ErrorCode.UNAUTHENTICATED);
          return;
        }
      } catch (IllegalArgumentException exception) {
        SecurityContextHolder.clearContext();
        responseWriter.write(response, 401, ErrorCode.UNAUTHENTICATED);
        return;
      }
    }
    filterChain.doFilter(request, response);
  }
}
