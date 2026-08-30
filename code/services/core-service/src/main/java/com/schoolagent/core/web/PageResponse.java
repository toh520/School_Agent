package com.schoolagent.core.web;

import java.util.List;

/** Zero-based page contract shared by future deterministic business endpoints. */
public record PageResponse<T>(List<T> items, int page, int size, long total, int totalPages) {

  public PageResponse {
    items = List.copyOf(items);
    if (page < 0 || size < 1 || total < 0 || totalPages < 0) {
      throw new IllegalArgumentException("Invalid pagination values");
    }
  }
}
