from fastapi import FastAPI


app = FastAPI(
    title='Fenmo Assessment App',
    version='0.1.0',
)


@app.get('/')
def read_root() -> dict[str, str]:
    return {
        'message': 'Fenmo assessment app is ready',
        'status': 'ok',
    }


@app.get('/health')
def read_health() -> dict[str, str]:
    return {'status': 'healthy'}

