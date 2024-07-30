# qna-web
POC application to implement Q&amp;A on a website utilizing the Langchain framework.

## Installation
1. Clone the repository.
2. Install python 3.12 virtual environment and activate it.
3. Install Poetry: 
    ```commandline
    pip install poetry
    ```
4. Install dependencies
    ```commandline
    poetry install
    ```

## Running the application
### Crawler
```commandline
poetry run crawler --max-seen-urls=3 https://gradio.app/
```
#### If successful, the crawler will save the URLs and output a message to the console:
```text
INFO - Written 3 urls to gradio.app-urls.txt
```
#### You can get usage information by running:
```commandline
poetry run crawler --help 
```

### Process URLs (data preparation)
#### ⚠️ Ensure that .env file is present in the root directory with the `OPENAI_API_KEY` variable set.

```commandline
poetry run process_urls gradio.app-urls.txt
```
#### If successful, the process_urls script will output the following messages to the console:
```text
...
INFO - Saved index to html_vector_index
...
INFO - Saved index to text_vector_index
...
INFO - Report saved to report.csv
```
#### You can get usage information by running:
```commandline
poetry run process_urls --help 
```
