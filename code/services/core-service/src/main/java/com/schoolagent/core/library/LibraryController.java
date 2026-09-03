package com.schoolagent.core.library;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.library.LibraryDtos.BookResponse;
import com.schoolagent.core.library.LibraryDtos.LoanResponse;
import com.schoolagent.core.web.ApiResponse;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Student catalog and borrowing API; all mutations are scoped to the current identity. */
@RestController
@RequestMapping("/api/v1/library")
@PreAuthorize("hasRole('STUDENT')")
public class LibraryController {
  private final LibraryService service;

  public LibraryController(LibraryService service) {
    this.service = service;
  }

  @GetMapping("/books")
  public ApiResponse<List<BookResponse>> books(
      @RequestParam(required = false) String query,
      @RequestParam(required = false) String category,
      @RequestParam(required = false) String tag,
      @RequestParam(required = false) Boolean availableOnly) {
    return ApiResponse.success(service.books(query, category, tag, availableOnly), requestId());
  }

  @GetMapping("/books/{bookId}")
  public ApiResponse<BookResponse> book(@PathVariable UUID bookId) {
    return ApiResponse.success(service.book(bookId), requestId());
  }

  @GetMapping("/loans")
  public ApiResponse<List<LoanResponse>> loans(Authentication authentication) {
    return ApiResponse.success(service.loans(id(authentication)), requestId());
  }

  @PostMapping("/books/{bookId}/borrow")
  public ApiResponse<LoanResponse> borrow(
      Authentication authentication, @PathVariable UUID bookId) {
    return ApiResponse.success(service.borrow(id(authentication), bookId), requestId());
  }

  @PostMapping("/loans/{loanId}/return")
  public ApiResponse<LoanResponse> returnBook(
      Authentication authentication, @PathVariable UUID loanId) {
    return ApiResponse.success(service.returnBook(id(authentication), loanId), requestId());
  }

  private UUID id(Authentication auth) {
    return CurrentIdentity.from(auth).userId();
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
