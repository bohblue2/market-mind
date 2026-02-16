import hashlib
from datetime import datetime
from typing import Any

import pytz  # type: ignore
from sqlalchemy import select

from mm_crawler.database.models import (
    DocumentOrm,
    DocumentVersionOrm,
    IngestionEventOrm,
)
from mm_crawler.database.session import SessionLocal
from mm_crawler.items.canonical import CanonicalDocumentItem

kst = pytz.timezone("Asia/Seoul")


class CanonicalDocumentPipeline:
    def open_spider(self, spider):
        self.sess = SessionLocal()

    def close_spider(self, spider):
        self.sess.close()

    def process_item(self, item: CanonicalDocumentItem, spider):
        if not isinstance(item, CanonicalDocumentItem):
            return item
        source_code = str(item["source_code"])
        stream_key = str(item["stream_key"])
        external_id = str(item["external_id"])
        content_text = str(item.get("content_text") or "")
        content_hash = str(
            item.get("content_hash")
            or hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        )
        published_at = _normalize_datetime(item.get("published_at"))

        existing = self.sess.execute(
            select(DocumentOrm).where(
                DocumentOrm.source_code == source_code,
                DocumentOrm.external_id == external_id,
            )
        ).scalar_one_or_none()

        inserted = False
        updated = False
        if existing is None:
            document = DocumentOrm(
                source_code=source_code,
                stream_key=stream_key,
                external_id=external_id,
                canonical_url=str(item.get("canonical_url") or ""),
                title=item.get("title"),
                published_at=published_at,
                content_text=content_text,
                content_hash=content_hash,
                metadata_json=item.get("metadata_json"),
            )
            self.sess.add(document)
            self.sess.flush()
            inserted = True
        else:
            document = existing
            if document.content_hash != content_hash:
                document.content_text = content_text
                document.content_hash = content_hash
                document.title = item.get("title") or document.title
                document.published_at = published_at or document.published_at
                document.metadata_json = item.get("metadata_json")
                updated = True

        version_exists = self.sess.execute(
            select(DocumentVersionOrm).where(
                DocumentVersionOrm.document_id == document.id,
                DocumentVersionOrm.content_hash == content_hash,
            )
        ).scalar_one_or_none()

        if version_exists is None:
            self.sess.add(
                DocumentVersionOrm(
                    document_id=document.id,
                    content_hash=content_hash,
                    content_text=content_text,
                    metadata_json=item.get("metadata_json"),
                )
            )

        event_type = "inserted" if inserted else "updated" if updated else "unchanged"
        self.sess.add(
            IngestionEventOrm(
                source_code=source_code,
                stream_key=stream_key,
                external_id=external_id,
                event_type=event_type,
                status="success",
                payload_json={"content_hash": content_hash},
            )
        )
        self.sess.commit()
        return item


def _normalize_datetime(value: Any):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else kst.localize(value)
    if isinstance(value, str):
        for pattern in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y.%m.%d %H:%M",
            "%Y.%m.%d",
        ):
            try:
                parsed = datetime.strptime(value.strip(), pattern)
                return kst.localize(parsed)
            except ValueError:
                continue
    return None
