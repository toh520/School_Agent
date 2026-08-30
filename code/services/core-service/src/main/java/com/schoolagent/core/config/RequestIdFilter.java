package com.schoolagent.core.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** Creates a safe request identifier shared by responses, logs and downstream calls. */
@Component
public class RequestIdFilter extends OncePerRequestFilter {

  public static final String REQUEST_ID_HEADER = "X-Request-ID";
  public static final String MDC_KEY = "requestId";
  private static final Pattern SAFE_REQUEST_ID = Pattern.compile("[A-Za-z0-9._-]{1,80}");

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
      throws ServletException, IOException {
    String requestId = normalizedRequestId(request.getHeader(REQUEST_ID_HEADER));
    MDC.put(MDC_KEY, requestId);
    response.setHeader(REQUEST_ID_HEADER, requestId);
    try {
      filterChain.doFilter(request, response);
    } finally {
      MDC.remove(MDC_KEY);
    }
  }

  static String normalizedRequestId(String supplied) {
    if (supplied != null && SAFE_REQUEST_ID.matcher(supplied).matches()) {
      return supplied;
    }
    return UUID.randomUUID().toString();
  }
}
