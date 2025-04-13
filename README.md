# 🔍 CISI Search Interface – Next.js + Flask + Elasticsearch

This project is a web-based search interface built with **Next.js** that allows users to search and retrieve documents from the **CISI dataset** via a **Flask API backed by Elasticsearch**.

## 📚 About

The application consists of:

- **Frontend:** Built with Next.js (React), featuring a responsive search bar and result display.
- **Backend:** A Flask REST API that connects to Elasticsearch and indexes the CISI dataset.
- **Dataset:** The [CISI (Information Retrieval) dataset](https://ir.dcs.gla.ac.uk/resources/test_collections/cisi/) commonly used in information retrieval research.

## 🌐 Live Demo

> 🟢 [https://your-deployed-url.com](https://your-deployed-url.com)  
*(Replace with your deployed frontend URL)*

## 🚀 Features

- Full-text search across the CISI dataset
- Instant search with autocomplete
- Clean, responsive UI using React
- Fast query results using Elasticsearch
- Environment-configurable API base URL

## 🧱 Tech Stack

- **Frontend:** Next.js, React
- **Backend:** Flask, Elasticsearch
- **Data:** CISI Dataset
- **Deployment:** Vercel (frontend), Render (backend) *(or customize based on your stack)*

## 🔧 Environment Variables

Set the API endpoint for the Flask server in `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=https://es-cisi.onrender.com
