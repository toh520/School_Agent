package com.schoolagent.core.management;

import com.schoolagent.core.management.ManagementDtos.FieldError;
import java.util.List;
import java.util.Map;

/** Normalized values and field-level failures produced before any database write. */
record ValidationResult(Map<String, Object> values, List<FieldError> errors, int completeness) {

  ValidationResult {
    values = Map.copyOf(values);
    errors = List.copyOf(errors);
  }

  boolean valid() {
    return errors.isEmpty();
  }
}
