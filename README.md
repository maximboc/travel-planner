# Travel Planner
## Environment Variables (.env)

To use the Travel Planner, you need to set up your API keys in a .env file at the root of the project:
```bash
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_SECRET_KEY=your_amadeus_secret_key
WEATHER_API_KEY=your_openweathermap_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT="travel-planner"
LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
```

You can also add the following environment variables if you want to specify a Hugging Face model:
```bash
MODEL_NAME="google/gemma-3-27b-it:nebius"
BASE_URL="https://router.huggingface.co/v1"
MODEL_PROVIDER="openai"
HF_TOKEN=your_huggingface_api_key
```

## API Key Sources

Flight API: Retrieve your key from [Amadeus for Developers](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/quick-start) 

Weather API: Get your key from [OpenWeatherMap](https://openweathermap.org/api)

Geo/Places API: Obtain your key from [Geoapify Places API](https://apidocs.geoapify.com/docs/places/)
