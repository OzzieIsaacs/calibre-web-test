import unittest
from unittest.mock import Mock

from base_test import acquire_resource, release_resource
from helper_ui import ui_class


class TestHelperUIParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.worker_port = str(acquire_resource("port", owner=cls))

    @classmethod
    def tearDownClass(cls):
        release_resource("port", cls.worker_port, owner=cls)
        super().tearDownClass()

    def setUp(self):
        class TestUI(ui_class):
            driver = Mock()
            check_element_on_page = Mock(return_value=None)

        self.ui = TestUI
        self.ui.worker_port = self.worker_port
        self.ui.driver.current_url = "http://127.0.0.1:{}/book/1".format(self.worker_port)

    @staticmethod
    def book(book_id, badge=""):
        return (
            '<div class="col book session">'
            '<div class="cover mb-2"><a href="/book/{0}">'
            '<span class="img"><img src="/cover/{0}">{1}</span></a></div>'
            '<div class="meta"><a href="/book/{0}"><p class="title">Book {0}</p></a>'
            '<p class="author"><a class="author-name" href="/author/1">Author</a></p>'
            '<p class="series"><a href="/series/1">Series</a> (2)</p>'
            '<div class="rating"><i class="bi bi-star-fill"></i></div>'
            '</div></div>'
        ).format(book_id, badge)

    def test_book_sections_and_read_badges(self):
        for extra_class in ("mb-4", "caliblur-index"):
            with self.subTest(theme=extra_class):
                self.ui.check_element_on_page.reset_mock()
                self.ui.driver.page_source = (
                    '<div class="{0} random-books discover"><div class="row">'
                    '{1}</div></div>'
                    '<div class="discover load-more {0}"><div class="filterheader">'
                    '<div>Not a book</div></div><div class="row">{2}{3}</div></div>'
                ).format(
                    extra_class,
                    self.book(1, '<span class="badge rounded-pill cover-check-badge"></span>'),
                    self.book(2, '<span class="badge read bi bi-check"></span>'),
                    self.book(3),
                )
                random, books, pages = self.ui.get_books_displayed()
                self.assertEqual([book["id"] for book in random], ["1"])
                self.assertEqual([book["id"] for book in books], ["2", "3"])
                self.assertTrue(random[0]["read"])
                self.assertTrue(books[0]["read"])
                self.assertFalse(books[1]["read"])
                self.assertEqual(random[0]["author"], ["Author"])
                self.assertEqual(random[0]["series_index"], "2")
                self.assertEqual(random[0]["rating"], 1)
                self.assertIsNone(pages)
                author_locator = (
                    "xpath",
                    "//div[contains(@class, 'random-books')]//a[@href='/author/1']",
                )
                self.ui.check_element_on_page.assert_any_call(
                    author_locator, ("class name", "random-books"))

    def test_pagination_markup(self):
        for markup in (
            '<a>1</a><a>2</a>',
            '<li class="page-item active"><a class="page-link">1</a></li>'
            '<li class="page-item"><a class="page-link">2</a></li>',
        ):
            with self.subTest(markup=markup):
                self.ui.driver.page_source = (
                    '<div class="pagination extra">{}</div>'.format(markup))
                self.assertEqual(self.ui.get_books_displayed()[2], ["1", "2"])

    def test_shelf_with_additional_layout_classes(self):
        self.ui.driver.page_source = (
            '<div class="row display-flex g-3">{}</div>'.format(
                self.book(1, '<span class="cover-check-badge"></span>')))
        books = self.ui().get_shelf_books_displayed()
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["title"], "Book 1")
        self.assertTrue(books[0]["read"])

    def test_ereader_dropdown_variants(self):
        for label in ("sendbtn2", "send-to-ereader"):
            for tag in ("button", "a"):
                with self.subTest(label=label, tag=tag):
                    self.ui.driver.page_source = (
                        '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
                        '<button id="sendbtn2">Send</button>'
                        '<ul aria-labelledby="{0}">'
                        '<li><{1}>EPUB</{1}></li><li><{1}>PDF</{1}></li></ul>'
                    ).format(label, tag)
                    details = self.ui.get_book_details()
                    self.assertEqual([item.text for item in details["kindle"]], ["EPUB", "PDF"])
                    self.ui.driver.find_element.assert_called_with("id", "sendbtn2")

    def test_boolean_custom_column_icons(self):
        for icon, expected in (
            ("bi-check", "ok"), ("bi-check-lg", "ok"),
            ("bi-x", "remove"), ("bi-x-lg", "remove"),
        ):
            with self.subTest(icon=icon):
                self.ui.driver.page_source = (
                    '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
                    '<div class="real_custom_columns">Boolean:'
                    '<span class="bi {}"></span></div>'.format(icon))
                details = self.ui.get_book_details()
                self.assertEqual(details["cust_columns"], [
                    {"Text": "Boolean", "value": expected}])

    def test_single_ereader_action_and_text_custom_column(self):
        self.ui.driver.page_source = (
            '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
            '<button id="sendbtn">EPUB</button>'
            '<div class="real_custom_columns">Text: <p>Value</p></div>')
        details = self.ui.get_book_details()
        self.assertEqual([item.text for item in details["kindle"]], ["EPUB"])
        self.ui.driver.find_element.assert_called_with("id", "sendbtn")
        self.assertEqual(details["cust_columns"], [{"Text": "Text", "value": "Value"}])

    def test_description_mixed_text_does_not_skip_ereader_actions(self):
        self.ui.driver.page_source = (
            '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
            '<div class="comments"><h3>Description:</h3>'
            'Before <p>Nested <strong>text</strong> tail</p> after</div>'
            '<button id="sendbtn2">Send</button>'
            '<ul aria-labelledby="sendbtn2"><li><button>EPUB</button></li></ul>')
        details = self.ui.get_book_details()
        self.assertEqual(details["comment"], "BeforeNestedtexttailafter")
        self.assertEqual([item.text for item in details["kindle"]], ["EPUB"])

    def test_empty_description(self):
        self.ui.driver.page_source = (
            '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
            '<div class="comments"><h3>Description:</h3></div>')
        self.assertEqual(self.ui.get_book_details()["comment"], "")

    def test_linked_and_plain_identifiers(self):
        self.ui.driver.page_source = (
            '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
            '<div class="identifiers"><p><span class="bi bi-link-45deg"></span>'
            '<a href="https://www.worldcat.org/isbn/123">ISBN</a>'
            '<span title="test">bookid</span></p></div>')
        self.assertEqual(self.ui.get_book_details()["identifier"], [
            {"ISBN": "https://www.worldcat.org/isbn/123"}, {"bookid": "test"}])

    def test_nested_custom_column_text(self):
        self.ui.driver.page_source = (
            '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
            '<div class="real_custom_columns">Comment:'
            '<p><strong>Nested</strong> text</p></div>')
        self.assertEqual(self.ui.get_book_details()["cust_columns"], [
            {"Text": "Comment", "value": "Nested text"}])

    def test_invalid_details_raise_instead_of_returning_partial_data(self):
        self.ui.driver.page_source = '<h2>Book</h2>'
        with self.assertRaisesRegex(AssertionError, "Could not parse book details"):
            self.ui.get_book_details()

    def test_missing_book_redirect_surfaces_flash_error(self):
        self.ui.driver.page_source = (
            '<h2>Books</h2><div id="flash_danger">Book not found</div>')
        self.assertEqual(self.ui.get_book_details(), {
            "id": 1, "error": "Book not found"})

    def test_detail_rating_excludes_sidebar_icons(self):
        self.ui.driver.page_source = (
            '<h2>Book</h2><div class="cover"><img src="/cover/1"></div>'
            '<nav><i class="bi bi-star-fill"></i></nav>'
            '<div class="rating"><i class="bi bi-star-fill"></i>'
            '<i class="bi bi-star-fill"></i><i class="bi bi-star"></i></div>')
        self.assertEqual(self.ui.get_book_details()["rating"], 2)
