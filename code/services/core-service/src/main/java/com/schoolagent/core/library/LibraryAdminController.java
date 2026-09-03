package com.schoolagent.core.library;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.library.LibraryDtos.BookResponse;
import com.schoolagent.core.library.LibraryDtos.LibraryBookUpsertRequest;
import com.schoolagent.core.web.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Combined book-and-holding administration for the single physical library. */
@RestController
@RequestMapping("/api/v1/admin/library/books")
@PreAuthorize("hasRole('INFO_ADMIN')")
public class LibraryAdminController {
  private final LibraryService service;

  public LibraryAdminController(LibraryService service) {
    this.service = service;
  }

  @GetMapping
  public ApiResponse<List<BookResponse>> books(@RequestParam(required = false) String query) {
    return ApiResponse.success(service.books(query, null, null, null), requestId());
  }

  @PostMapping
  public ApiResponse<BookResponse> create(
      Authentication authentication, @Valid @RequestBody LibraryBookUpsertRequest request) {
    return ApiResponse.success(service.create(request, id(authentication)), requestId());
  }

  @PutMapping("/{bookId}")
  public ApiResponse<BookResponse> update(
      Authentication authentication,
      @PathVariable UUID bookId,
      @Valid @RequestBody LibraryBookUpsertRequest request) {
    return ApiResponse.success(service.update(bookId, request, id(authentication)), requestId());
  }

  @DeleteMapping("/{bookId}")
  public ApiResponse<Void> deactivate(Authentication authentication, @PathVariable UUID bookId) {
    service.deactivate(bookId, id(authentication));
    return ApiResponse.success(null, requestId());
  }

  private UUID id(Authentication auth) {
    return CurrentIdentity.from(auth).userId();
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
