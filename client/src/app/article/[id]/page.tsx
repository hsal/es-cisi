'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { FaUser, FaFileAlt, FaArrowLeft } from 'react-icons/fa';
import { endpoints } from '@/utils/api';

type ArticleProps = {
  params: {
    id: string;
  };
};

type ArticleData = {
  author: string;
  doc_id: number;
  preprocessed_text: string;
  text: string;
  title: string;
};

const ArticlePage = ({ params: { id } }: ArticleProps) => {
  const [article, setArticle] = useState<ArticleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        const response = await fetch(endpoints.getDocumentById(id));

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setArticle(data);
      } catch (error) {
        console.error('Error fetching article:', error);
        setError('Failed to load article');
      } finally {
        setLoading(false);
      }
    };

    fetchArticle();
  }, [id]);

  if (loading) {
    return (
      <div className='max-w-4xl mx-auto p-6 flex justify-center items-center h-64'>
        <div className='animate-pulse text-xl'>Loading article...</div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className='max-w-4xl mx-auto p-6'>
        <div className='bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg'>
          {error || 'Article not found'}
        </div>
        <div className='mt-4'>
          <Link
            href='/'
            className='text-blue-600 hover:underline flex items-center'
          >
            <FaArrowLeft className='mr-2' />
            Back to search results
          </Link>
        </div>
      </div>
    );
  }

  // Format text with proper paragraph breaks
  const formattedText = article.text.split('\n').filter(Boolean);

  return (
    <div className='max-w-4xl mx-auto p-6'>
      <div className='mb-6'>
        <Link
          href='/'
          className='inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors'
        >
          <FaArrowLeft className='mr-2' />
          Back to search results
        </Link>
      </div>

      <div className='bg-white rounded-lg shadow-lg overflow-hidden'>
        {/* Header */}
        <div className='bg-gradient-to-r from-blue-700 to-blue-900 p-6 text-white'>
          <h1 className='text-3xl font-bold'>{article.title}</h1>
          <div className='mt-4 flex items-center'>
            <FaUser className='mr-2' />
            <span>{article.author}</span>
          </div>
          <div className='mt-2 text-blue-100 text-sm'>
            Document ID: {article.doc_id}
          </div>
        </div>

        {/* Content */}
        <div className='p-6'>
          <div className='mb-8'>
            <h2 className='text-xl font-semibold mb-3 text-gray-700 flex items-center'>
              <FaFileAlt className='mr-2 text-blue-600' />
              Article Content
            </h2>
            <div className='prose max-w-none'>
              {formattedText.map((paragraph, index) => (
                <p key={index} className='mb-4 text-gray-800 leading-relaxed'>
                  {paragraph}
                </p>
              ))}
            </div>
          </div>

          {/* Keywords/Summary Box */}
          <div className='bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6'>
            <h3 className='font-semibold text-blue-800 mb-2'>Summary</h3>
            <p className='text-gray-700'>{article.preprocessed_text}</p>
          </div>

          {/* Article Metadata */}
          <div className='border-t border-gray-200 pt-4 mt-6'>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div>
                <h4 className='font-medium text-gray-500'>Author</h4>
                <p>{article.author}</p>
              </div>
              <div>
                <h4 className='font-medium text-gray-500'>Document ID</h4>
                <p>{article.doc_id}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticlePage;
