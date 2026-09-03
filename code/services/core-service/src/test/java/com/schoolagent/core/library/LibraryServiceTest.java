package com.schoolagent.core.library;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.schoolagent.core.library.LibraryDtos.BookResponse;
import com.schoolagent.core.library.LibraryDtos.LoanResponse;
import com.schoolagent.core.web.BusinessException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;

@ExtendWith(MockitoExtension.class)
class LibraryServiceTest {
  @Mock private LibraryRepository repository;
  private LibraryService service;

  @BeforeEach
  void setUp() {
    service = new LibraryService(repository);
  }

  @Test
  void borrowRejectsDuplicateCurrentLoanBeforeChangingInventory() {
    UUID userId = UUID.randomUUID();
    BookResponse book = book(2);
    when(repository.lockBook(book.id())).thenReturn(Optional.of(book));
    when(repository.hasCurrentLoan(userId, book.id())).thenReturn(true);

    BusinessException error =
        assertThrows(BusinessException.class, () -> service.borrow(userId, book.id()));

    assertEquals(HttpStatus.CONFLICT, error.getStatus());
    verify(repository, never()).createLoan(userId, book);
  }

  @Test
  void borrowCreatesRecordForAvailableBook() {
    UUID userId = UUID.randomUUID();
    UUID loanId = UUID.randomUUID();
    BookResponse book = book(1);
    LoanResponse loan = loan(loanId, book.id(), "BORROWED", null);
    when(repository.lockBook(book.id())).thenReturn(Optional.of(book));
    when(repository.hasCurrentLoan(userId, book.id())).thenReturn(false);
    when(repository.createLoan(userId, book)).thenReturn(loanId);
    when(repository.loan(userId, loanId, false)).thenReturn(Optional.of(loan));

    assertEquals(loan, service.borrow(userId, book.id()));
    verify(repository).createLoan(userId, book);
  }

  @Test
  void returnRejectsAlreadyReturnedRecord() {
    UUID userId = UUID.randomUUID();
    UUID loanId = UUID.randomUUID();
    LoanResponse returned = loan(loanId, UUID.randomUUID(), "RETURNED", Instant.now());
    when(repository.loan(userId, loanId, true)).thenReturn(Optional.of(returned));

    BusinessException error =
        assertThrows(BusinessException.class, () -> service.returnBook(userId, loanId));

    assertEquals(HttpStatus.CONFLICT, error.getStatus());
    verify(repository, never()).returnLoan(loanId, userId);
  }

  private BookResponse book(int availableCount) {
    return new BookResponse(
        UUID.randomUUID(),
        UUID.randomUUID(),
        "BOOK-TEST",
        "测试图书",
        "9780000000001",
        List.of("作者"),
        "出版社",
        "第1版",
        2026,
        "中文",
        "小说",
        List.of("测试"),
        "简介",
        "",
        "I5/001",
        "一层书架",
        3,
        availableCount,
        availableCount > 0);
  }

  private LoanResponse loan(UUID loanId, UUID bookId, String status, Instant returnedAt) {
    return new LoanResponse(
        loanId, bookId, "测试图书", "", "作者", "I5/001", "一层书架", status, Instant.now(), returnedAt);
  }
}
