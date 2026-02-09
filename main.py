from __future__ import annotations

import argparse
from pathlib import Path

from gastric_agent.crawler import GastricCrawler
from gastric_agent.kb_builder import build_vector_db


DEFAULT_RAW_PATH = "data/raw/gastric_docs.jsonl"
DEFAULT_DB_DIR = "data/vector_db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="胃病数据处理命令")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl", help="抓取网页数据")
    crawl_parser.add_argument("--max-pages", type=int, default=120)
    crawl_parser.add_argument("--min-chars", type=int, default=500)
    crawl_parser.add_argument("--output", default=DEFAULT_RAW_PATH)

    index_parser = subparsers.add_parser("index", help="构建向量索引")
    index_parser.add_argument("--input", default=DEFAULT_RAW_PATH)
    index_parser.add_argument("--persist-dir", default=DEFAULT_DB_DIR)
    index_parser.add_argument("--chunk-size", type=int, default=700)
    index_parser.add_argument("--chunk-overlap", type=int, default=120)

    prep_parser = subparsers.add_parser("prepare", help="抓取并构建向量索引")
    prep_parser.add_argument("--max-pages", type=int, default=120)
    prep_parser.add_argument("--min-chars", type=int, default=500)
    prep_parser.add_argument("--output", default=DEFAULT_RAW_PATH)
    prep_parser.add_argument("--persist-dir", default=DEFAULT_DB_DIR)
    prep_parser.add_argument("--chunk-size", type=int, default=700)
    prep_parser.add_argument("--chunk-overlap", type=int, default=120)

    return parser


def run_crawl(max_pages: int, min_chars: int, output: str) -> None:
    crawler = GastricCrawler()

    def show_progress(
        saved_docs: int,
        target_docs: int,
        visited_pages: int,
        queued_pages: int,
        current_url: str,
    ) -> None:
        print(
            (
                "\rCrawling... "
                f"saved={saved_docs}/{target_docs} "
                f"visited={visited_pages} "
                f"queue={queued_pages} "
                f"current={current_url[:70]}"
            ),
            end="",
            flush=True,
        )

    docs = crawler.crawl(
        max_pages=max_pages,
        min_chars=min_chars,
        on_progress=show_progress,
    )
    print()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    crawler.save_jsonl(docs, output)
    print(f"Crawl done: {len(docs)} docs saved to {output}")


def run_index(
    input_path: str, persist_dir: str, chunk_size: int, chunk_overlap: int
) -> None:
    chunks = build_vector_db(
        jsonl_path=input_path,
        persist_dir=persist_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    print(f"Index done: {chunks} chunks stored in {persist_dir}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "crawl":
        run_crawl(args.max_pages, args.min_chars, args.output)
        return

    if args.command == "index":
        run_index(args.input, args.persist_dir, args.chunk_size, args.chunk_overlap)
        return

    if args.command == "prepare":
        run_crawl(args.max_pages, args.min_chars, args.output)
        run_index(args.output, args.persist_dir, args.chunk_size, args.chunk_overlap)
        return

    parser.error("Unknown command")


if __name__ == "__main__":
    main()
