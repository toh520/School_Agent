package com.schoolagent.core.library;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

/** Public contracts for catalog browsing, combined administration, and demo loans. */
public final class LibraryDtos {
  private LibraryDtos() {}

  public record BookResponse(
      UUID id,
      UUID holdingId,
      String code,
      String name,
      String isbn,
      List<String> authors,
      String publisher,
      String edition,
      Integer publishedYear,
      String language,
      String category,
      List<String> tags,
      String summary,
      String coverImage,
      String callNumber,
      String location,
      int totalCount,
      int availableCount,
      boolean available) {}

  public record LoanResponse(
      UUID id,
      UUID bookId,
      String bookName,
      String coverImage,
      String authors,
      String callNumber,
      String location,
      String status,
      Instant borrowedAt,
      Instant returnedAt) {}

  public record LibraryBookUpsertRequest(
      @NotBlank @Size(max = 120) String name,
      @NotBlank @Pattern(regexp = "(?:97[89])?[0-9Xx-]{10,17}") String isbn,
      @NotEmpty @Size(max = 8) List<@NotBlank @Size(max = 80) String> authors,
      @Size(max = 120) String publisher,
      @Size(max = 80) String edition,
      @Min(1000) @Max(2100) Integer publishedYear,
      @Size(max = 40) String language,
      @NotBlank @Size(max = 60) String category,
      @Size(max = 20) List<@NotBlank @Size(max = 40) String> tags,
      @Size(max = 4000) String summary,
      @Size(max = 1400000) String coverImage,
      @NotBlank @Size(max = 80) String callNumber,
      @NotBlank @Size(max = 120) String location,
      @Min(0) @Max(100000) int totalCount,
      @Min(0) @Max(100000) int availableCount) {}
}
