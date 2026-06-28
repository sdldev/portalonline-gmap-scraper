"""Tests for scraper module."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from portalonline_gmap_scraper.scraper import (
    _COLLECT_LINKS_JS,
    _EXTRACT_DATA_JS,
    _block_heavy_resources,
    _get_available_ram_mb,
    _memory_guard,
    _random_delay,
    collect_lead_links,
    extract_lead_data,
    process_all_leads,
    scrape,
)


class TestBlockedResources:
    @pytest.mark.asyncio
    async def test_block_image_resources(self):
        route = AsyncMock()
        route.request.resource_type = "image"
        await _block_heavy_resources(route)
        route.abort.assert_called_once()
        route.continue_.assert_not_called()

    @pytest.mark.asyncio
    async def test_block_media_resources(self):
        route = AsyncMock()
        route.request.resource_type = "media"
        await _block_heavy_resources(route)
        route.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_block_font_resources(self):
        route = AsyncMock()
        route.request.resource_type = "font"
        await _block_heavy_resources(route)
        route.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_allow_document_resources(self):
        route = AsyncMock()
        route.request.resource_type = "document"
        await _block_heavy_resources(route)
        route.continue_.assert_called_once()
        route.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_allow_script_resources(self):
        route = AsyncMock()
        route.request.resource_type = "script"
        await _block_heavy_resources(route)
        route.continue_.assert_called_once()


class TestJavaScriptExtraction:
    def test_extract_data_js_is_string(self):
        assert isinstance(_EXTRACT_DATA_JS, str)
        assert "document.querySelector" in _EXTRACT_DATA_JS

    def test_collect_links_js_is_string(self):
        assert isinstance(_COLLECT_LINKS_JS, str)
        assert "document.querySelectorAll" in _COLLECT_LINKS_JS


class TestResourceManagement:
    def test_get_available_ram_returns_int(self):
        result = _get_available_ram_mb()
        assert isinstance(result, int)
        assert result > 0

    @pytest.mark.asyncio
    async def test_memory_guard_no_pause_when_enough_ram(self):
        with patch(
            "portalonline_gmap_scraper.scraper._get_available_ram_mb",
            return_value=99999,
        ):
            paused = await _memory_guard()
            assert paused is False

    @pytest.mark.asyncio
    async def test_memory_guard_pauses_when_low_ram(self):
        with patch(
            "portalonline_gmap_scraper.scraper._get_available_ram_mb", return_value=100
        ):
            with patch("portalonline_gmap_scraper.scraper.asyncio.sleep") as mock_sleep:
                paused = await _memory_guard()
                assert paused is True
                mock_sleep.assert_called_once()


class TestCollectLeadLinks:
    @pytest.mark.asyncio
    async def test_returns_empty_list_on_feed_failure(self):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        mock_page.wait_for_selector.side_effect = Exception("Feed not found")
        mock_page.get_by_role = Mock(return_value=AsyncMock())

        result = await collect_lead_links(mock_browser, "test query", target=5)

        assert result == []
        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_limited_links(self):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        mock_page.get_by_role = Mock(return_value=AsyncMock())

        mock_page.evaluate.return_value = [
            "https://maps.google.com/place/1",
            "https://maps.google.com/place/2",
            "https://maps.google.com/place/3",
        ]

        result = await collect_lead_links(mock_browser, "test query", target=2)

        assert len(result) == 2
        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_streams_links_to_queue(self):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        mock_page.get_by_role = Mock(return_value=AsyncMock())
        mock_page.evaluate.return_value = [
            "https://maps.google.com/place/1",
            "https://maps.google.com/place/2",
            "https://maps.google.com/place/3",
        ]

        url_queue: asyncio.Queue[str | None] = asyncio.Queue()
        result = await collect_lead_links(
            mock_browser, "test query", target=2, url_queue=url_queue
        )

        queued = [await url_queue.get(), await url_queue.get()]
        assert len(result) == 2
        assert set(queued) == set(result)


class TestExtractLeadData:
    @pytest.mark.asyncio
    async def test_returns_data_on_success(self):
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = {
            "name": "Test Business",
            "address": "123 Test St",
            "phone": "555-1234",
            "website": "https://example.com",
        }

        result = await extract_lead_data(mock_page, "https://maps.google.com/place/1")

        assert result is not None
        assert result["name"] == "Test Business"
        assert result["address"] == "123 Test St"

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self):
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("Navigation failed")

        result = await extract_lead_data(mock_page, "https://maps.google.com/place/1")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_null_data(self):
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = None

        result = await extract_lead_data(mock_page, "https://maps.google.com/place/1")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_navigation_timeout(self):
        mock_page = AsyncMock()
        mock_page.goto.side_effect = TimeoutError("Navigation timeout")

        result = await extract_lead_data(mock_page, "https://maps.google.com/place/1")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_selector_timeout(self):
        mock_page = AsyncMock()
        mock_page.wait_for_selector.side_effect = TimeoutError("Selector timeout")

        result = await extract_lead_data(mock_page, "https://maps.google.com/place/1")

        assert result is None
        mock_page.evaluate.assert_not_called()


class TestRandomDelay:
    @pytest.mark.asyncio
    async def test_random_delay_within_bounds(self):
        import time

        start = time.monotonic()
        await _random_delay()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.5  # at least close to DELAY_MIN_SEC


class TestProcessAllLeads:
    @pytest.mark.asyncio
    async def test_processes_urls_concurrently(self):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        mock_browser.new_page.return_value = mock_page

        urls = ["url1", "url2", "url3"]

        with (
            patch(
                "portalonline_gmap_scraper.scraper.extract_lead_data_with_retry",
                return_value={
                    "name": "Business",
                    "address": "Address",
                    "phone": "Phone",
                    "website": "Website",
                },
            ),
            patch("portalonline_gmap_scraper.scraper._random_delay"),
            patch(
                "portalonline_gmap_scraper.scraper._memory_guard",
                return_value=False,
            ),
        ):
            result = await process_all_leads(mock_browser, urls, batch_size=100)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_respects_max_tabs(self):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        urls = ["url1", "url2", "url3"]
        # Set max_tabs to 1, should only create 1 page
        await process_all_leads(mock_browser, urls, max_tabs=1)

        assert mock_browser.new_page.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_empty_url_list(self):
        mock_browser = AsyncMock()
        result = await process_all_leads(mock_browser, [])
        assert result == []


class TestScrape:
    @pytest.mark.asyncio
    async def test_scrape_returns_empty_on_no_leads(self):
        with patch("portalonline_gmap_scraper.scraper.AsyncCamoufox") as mock_camoufox:
            mock_browser = AsyncMock()
            mock_camoufox.return_value.__aenter__.return_value = mock_browser

            with patch(
                "portalonline_gmap_scraper.scraper.collect_lead_links", return_value=[]
            ):
                result = await scrape("test query")
                assert result == []

    @pytest.mark.asyncio
    async def test_scrape_processes_leads(self):
        with patch("portalonline_gmap_scraper.scraper.AsyncCamoufox") as mock_camoufox:
            mock_browser = AsyncMock()
            mock_camoufox.return_value.__aenter__.return_value = mock_browser

            mock_urls = ["url1", "url2"]
            mock_pages = [AsyncMock(), AsyncMock()]
            mock_browser.new_page.side_effect = mock_pages

            async def fake_collect(_, __, target=25, skip_urls=None, max_urls=60):
                return mock_urls[:target]

            async def fake_extract(_, url):
                return {
                    "name": f"Business {url[-1]}",
                    "phone": "08123456789",
                    "address": "Addr",
                    "website": "N/A",
                }

            with (
                patch(
                    "portalonline_gmap_scraper.scraper.collect_lead_links",
                    side_effect=fake_collect,
                ),
                patch(
                    "portalonline_gmap_scraper.scraper.extract_lead_data_with_retry",
                    side_effect=fake_extract,
                ),
                patch("portalonline_gmap_scraper.scraper._random_delay"),
                patch(
                    "portalonline_gmap_scraper.scraper._memory_guard",
                    return_value=False,
                ),
            ):
                result = await scrape(
                    "test query", target=2, max_tabs=2, batch_size=100
                )
                assert len(result) == 2
                assert {item["name"] for item in result} == {
                    "Business 1",
                    "Business 2",
                }

    @pytest.mark.asyncio
    async def test_scrape_negative_target_returns_empty(self):
        result = await scrape("test query", target=-1)
        assert result == []
