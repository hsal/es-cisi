import React from 'react';

import { SearchQueryPropTypes } from '../global/SearchBar';
import Link from 'next/link';

type ResultsListViewProps = {
  searchResults: SearchQueryPropTypes[];
};

const ResultsListView: React.FC<ResultsListViewProps> = ({ searchResults }) => {
  return (
    <div className='mt-6 w-full max-w-2xl bg-white shadow-lg rounded-lg p-4'>
      {searchResults.map((result) => (
        <div key={result.doc_id} className='border-b last:border-0 pb-4 mb-4'>
          <Link href={`/article/${result.doc_id}`} passHref>
            <h3 className='text-xl font-semibold text-blue-600 hover:underline cursor-pointer'>
              {result.title}
            </h3>
          </Link>
          <p className='text-gray-600 text-sm'>By {result.author}</p>
          <p className='text-gray-800 mt-2'>
            {result.highlights.text.map((snippet, index) => (
              <span key={index} dangerouslySetInnerHTML={{ __html: snippet }} />
            ))}
          </p>
        </div>
      ))}
    </div>
  );
};

export default ResultsListView;
