---
title: Insight Facilitator
emoji: ✨
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.25.0
app_file: app.py
pinned: false
python_version: 3.12
license: cc-by-nc-4.0
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# Insight Facilitator

Insight Facilitator generates profound insights and thought-provoking discussion questions for any book or movie. Powered by OpenAI GPT-4o, it uses a streamlined system of autonomous AI agents to deliver a focused analysis tailored to the specific media type.

## How It Works

Insight Facilitator uses three specialized AI agents working in sequence:

1. **Information Gatherer**: Researches the book or movie, finding plot details, themes, character information, and critical reception

2. **Insight Analyst**: Analyzes the research to generate insights about themes, character development, artistic techniques, and deeper meanings

3. **Discussion Facilitator**: Creates thought-provoking discussion questions perfect for book clubs, film discussions, or personal reflection

## Features

- **Deep Analysis**: Goes beyond surface-level summaries to provide meaningful insights
- **Discussion Ready**: Creates questions that spark engaging conversations
- **OpenAI Powered**: Utilizes GPT-4o for comprehensive analysis
- **Streamlined Interface**: Clean design with focused input areas

## Usage

1. Enter any book or movie title
2. Select the media type (Book or Movie)
3. Click "Generate Insights & Discussion Questions"
4. Receive insights and discussion questions

**Note**: Analysis takes 2-3 minutes to complete.

## API Keys Required

This application requires an API key to function. You'll need to add this as a secret in your Hugging Face Space:

- `OPENAI_API_KEY` - Required for OpenAI GPT-4o

## About

Insight Facilitator is perfect for book clubs, film discussion groups, literature teachers, film students, or anyone who wants to deepen their understanding of books and movies.

Created with CrewAI, a framework for orchestrating role-playing AI agents.

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](http://creativecommons.org/licenses/by-nc/4.0/).

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

You are free to use, share, and adapt this work for non-commercial purposes, as long as you provide attribution.
