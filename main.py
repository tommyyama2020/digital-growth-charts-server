# standard imports
import json
from pathlib import Path
import yaml

# third party imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseSettings

# local / rcpch imports
from rcpchgrowth import chart_functions, constants
from routers import trisomy_21, turners, uk_who


### API VERSION ###
version = '3.0.3'  # this is set by bump version.


# Declare the FastAPI app
app = FastAPI(
        openapi_url="/",
        redoc_url=None,
        license_info={
            "name": "GNU Affero General Public License",
            "url": "https://www.gnu.org/licenses/agpl-3.0.en.html"
            },
    )


# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*', 'http://localhost:8000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers for each type of endpoint.
app.include_router(uk_who)
app.include_router(turners)
app.include_router(trisomy_21)


# Customise API metadata
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="RCPCH Digital Growth API",
        version=version,
        description="Returns SDS and centiles for child growth measurements using growth references. Currently provides calculations based on the UK-WHO, Turner's Syndrome and Trisomy-21 references.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Include the root endpoint (so it is _described_ in the APIspec).
@app.get("/", tags=["openapi3"])
def root():
    """
    # API spec endpoint
    * The root `/` API endpoint returns the openAPI3 specification in JSON format
    * This spec is also available in the root of the server code repository, in JSON and YAML
    """
    return


# Generate and store the chart plotting data for the centile background curves.
# This data is only generated once and then is stored and served from file.
def generate_and_store_chart_data():
    for reference in constants.REFERENCES:
        for sex in constants.SEXES:
            for measurement_method in constants.MEASUREMENT_METHODS:
                # Don't generate files for Turner's for references we don't have (males or non-height measurements)
                if reference == "turners-syndrome" and (sex != "female" or measurement_method != "height"):
                    continue
                chart_data_file = Path(
                    f'chart-data/{reference}-{sex}-{measurement_method}.json')
                if chart_data_file.exists():
                    print(f'Chart data file exists for {reference}-{sex}-{measurement_method}.')
                else:
                    print(f'Chart data file does not exist for {reference}-{sex}-{measurement_method}')
                    try:
                        chart_data = chart_functions.create_chart(
                            reference,
                            measurement_method=measurement_method,
                            sex=sex,
                            centile_selection=constants.COLE_TWO_THIRDS_SDS_NINE_CENTILES
                        )
                        with open(f'chart-data/{reference}-{sex}-{measurement_method}.json', 'w') as file:
                            file.write(json.dumps(chart_data, indent=4))
                        print(f'chart data file created for {reference}-{sex}-{measurement_method}')
                    except Exception as error:
                        print(error)

generate_and_store_chart_data()


# Saves openAPI3 spec to file in the project root.
def write_apispec_to_file():
    if Path('openapi.yml').exists():
        print(f'openAPI3 YAML file exists')
    else:
        print(f'openAPI3 YAML file created')
        with open(r'openapi.yml', 'w') as file:
            file.write(yaml.dump(app.openapi_schema))
            
    if Path('openapi.json').exists():
        print(f'openAPI3 JSON file exists')
    else:
        print(f'openAPI3 JSON file created')
        with open(r'openapi.json', 'w') as file:
            file.write(json.dumps(
                app.openapi_schema,
                indent=4)
                )
    
write_apispec_to_file()
