package com.schoolagent.core.management;

import java.util.List;

/** One managed field and its user-facing validation metadata. */
public record FieldDefinition(
    String key,
    String label,
    FieldKind kind,
    boolean required,
    boolean recommended,
    List<String> options,
    String help) {

  public FieldDefinition {
    options = options == null ? List.of() : List.copyOf(options);
  }
}
