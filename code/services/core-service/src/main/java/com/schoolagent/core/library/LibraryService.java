package com.schoolagent.core.library;

import com.schoolagent.core.library.LibraryDtos.BookResponse;
import com.schoolagent.core.library.LibraryDtos.LibraryBookUpsertRequest;
import com.schoolagent.core.library.LibraryDtos.LoanResponse;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.util.List;
import java.util.UUID;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Applies inventory, ownership, and duplicate-loan rules outside the UI and model. */
@Service
class LibraryService {
  private final LibraryRepository repository;

  LibraryService(LibraryRepository repository) {
    this.repository = repository;
  }

  List<BookResponse> books(String query, String category, String tag, Boolean availableOnly) {
    return repository.books(query, category, tag, availableOnly);
  }

  BookResponse book(UUID bookId) {
    return repository.book(bookId).orElseThrow(() -> missing());
  }

  List<LoanResponse> loans(UUID userId) {
    return repository.loans(userId);
  }

  @Transactional
  LoanResponse borrow(UUID userId, UUID bookId) {
    BookResponse book = repository.lockBook(bookId).orElseThrow(() -> missing());
    if (!book.available() || book.availableCount() <= 0) throw conflict();
    if (repository.hasCurrentLoan(userId, bookId)) throw conflict();
    try {
      UUID loanId = repository.createLoan(userId, book);
      return repository.loan(userId, loanId, false).orElseThrow();
    } catch (DataIntegrityViolationException exception) {
      throw conflict();
    }
  }

  @Transactional
  LoanResponse returnBook(UUID userId, UUID loanId) {
    LoanResponse loan = repository.loan(userId, loanId, true).orElseThrow(() -> missing());
    if (!"BORROWED".equals(loan.status())) throw conflict();
    repository.returnLoan(loanId, userId);
    return repository.loan(userId, loanId, false).orElseThrow();
  }

  @Transactional
  BookResponse create(LibraryBookUpsertRequest request, UUID actorId) {
    validateCounts(request);
    return repository.createCombined(request, actorId);
  }

  @Transactional
  BookResponse update(UUID bookId, LibraryBookUpsertRequest request, UUID actorId) {
    validateCounts(request);
    repository.book(bookId).orElseThrow(() -> missing());
    return repository.updateCombined(bookId, request, actorId);
  }

  @Transactional
  void deactivate(UUID bookId, UUID actorId) {
    repository.book(bookId).orElseThrow(() -> missing());
    if (repository.hasOutstandingLoans(bookId)) throw conflict();
    repository.deactivateCombined(bookId, actorId);
  }

  private void validateCounts(LibraryBookUpsertRequest request) {
    if (request.availableCount() > request.totalCount()) throw conflict();
  }

  private BusinessException missing() {
    return new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND);
  }

  private BusinessException conflict() {
    return new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
  }
}
