.PHONY: help install data signals backtest robust figures paper test all clean

help:
	@echo "Targets: install | data | signals | backtest | robust | figures | paper | test | all | clean"

install:
	uv sync --extra dev

data:
	uv run qmj data prices
	uv run qmj data benchmarks
	uv run qmj data ken-french

signals:
	uv run qmj signals paper-q

backtest:
	uv run qmj backtest

robust:
	uv run qmj robust

figures:
	uv run qmj figure cumret

paper:
	typst compile paper/main.typ

paper-watch:
	typst watch paper/main.typ

test:
	uv run pytest -q

all: install data signals backtest robust figures paper

clean:
	rm -rf data/interim/* data/processed/*
	rm -f paper/main.pdf
