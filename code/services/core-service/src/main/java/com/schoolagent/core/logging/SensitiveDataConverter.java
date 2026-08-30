package com.schoolagent.core.logging;

import ch.qos.logback.classic.pattern.ClassicConverter;
import ch.qos.logback.classic.spi.ILoggingEvent;
import java.util.regex.Pattern;

/** Masks common secret assignments before a message reaches a log appender. */
public class SensitiveDataConverter extends ClassicConverter {

  private static final Pattern SECRET_ASSIGNMENT =
      Pattern.compile(
          "(?i)(password|passwd|token|secret|api[_-]?key|authorization)"
              + "(\\s*[=:]\\s*)([^\\s,;]+)");

  @Override
  public String convert(ILoggingEvent event) {
    return mask(event.getFormattedMessage());
  }

  public static String mask(String message) {
    if (message == null) {
      return "";
    }
    return SECRET_ASSIGNMENT.matcher(message).replaceAll("$1$2***");
  }
}
