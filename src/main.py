import uvicorn


def main() -> None:
    uvicorn.run("src.api:app", host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
