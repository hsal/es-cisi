import React from 'react';
import ResultsListView from '../ui/ResultsListView';
import { SearchBox, SearchProvider } from '@elastic/react-search-ui';
import { endpoints } from '@/utils/api';

export type SearchQueryPropTypes = {
  author: string;
  doc_id: number;
  highlights: {
    author: string[];
    text: string[];
    title: string[];
  };
  score: number;
  text: string;
  title: string;
};

const SearchBar = () => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [searchResults, setSearchResults] =
    React.useState<SearchQueryPropTypes[]>();

  const handleSearch = async (query: string) => {
    try {
      const response = await fetch(endpoints.search(query));

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setSearchResults(data.results);
    } catch (error) {
      console.error('Error fetching search results:', error);
    }
  };

  const apiConnector = {
    onAutocomplete: async ({ searchTerm }: { searchTerm: string }) => {
      const response = await fetch(endpoints.autocomplete(searchTerm));
      const data = await response.json();
      return {
        autocompletedResults: data.suggestions || [],
      };
    },

    onSearch: async (state: { searchTerm?: string }) => {
      const searchTerm = state.searchTerm || '';
      const response = await fetch(endpoints.search(searchTerm));
      const data = await response.json();

      return {
        results: data.results || [],
        totalResults: data.results?.length || 0,
        resultSearchTerm: searchTerm,
        totalPages: Math.ceil((data.results?.length || 0) / 10),
        pagingStart: 1,
        pagingEnd: data.results?.length || 0,
        wasSearched: true,
      };
    },

    onResultClick: ({ result }: { result: any }) => {
      console.log('Result clicked:', result);
    },

    onAutocompleteResultClick: ({ result }: { result: any }) => {
      console.log('Autocomplete result clicked:', result);
    },
  };

  const SearchProviderConfig = {
    apiConnector,
  };

  return (
    <div className='flex flex-col justify-center items-center w-full mt-36'>
      <h1 className='text-6xl font-bold mb-4'>
        <span className='text-blue-600'>G</span>
        <span className='text-red-600'>h</span>
        <span className='text-yellow-400'>a</span>
        <span className='text-green-600'>r</span>
      </h1>
      <SearchProvider
        // @ts-ignore
        config={{
          ...SearchProviderConfig,
        }}
      >
        <SearchBox
          inputProps={{
            className:
              'border border-gray-300 rounded-full p-4 pl-8 shadow-sm text-lg placeholder-gray-600 custom-search-input',
            placeholder: 'Search Ghar or type a query',
            value: searchQuery,
            onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
              setSearchQuery(e.target.value);
            },
          }}
          debounceLength={300}
          searchAsYouType={true}
          autocompleteResults={{
            titleField: 'name',
            urlField: 'url',
          }}
          autocompleteSuggestions={true}
          shouldClearFilters={true}
          autocompleteView={({ autocompletedResults, getItemProps }) => {
            return (
              <div className='sui-search-box__autocomplete-container'>
                {autocompletedResults.map((result, i) => (
                  <div
                    {...getItemProps({
                      key: result.doc_id || i.toString(),
                      index: i,
                      item: result,
                    })}
                    key={result.doc_id || i}
                    className='p-4 hover:bg-gray-200 cursor-pointer bg-white'
                  >
                    {result.snippet && (
                      <div className='flex items-center'>
                        <div>
                          <h2
                            className='text-lg font-semibold'
                            dangerouslySetInnerHTML={{
                              __html: result.snippet.replace(
                                /<mark>(.*?)<\/mark>/g,
                                '<strong>$1</strong>'
                              ),
                            }}
                          />
                          <p className='text-gray-500'>{result.title}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            );
          }}
          onSelectAutocomplete={(result: {
            title: string;
            snippet: string;
          }) => {
            if (result) {
              const query = result.snippet.replace(
                /<mark>(.*?)<\/mark>/g,
                '$1'
              );
              setSearchQuery(query);
              handleSearch(query);
            }
          }}
          onSubmit={(searchTerm) => {
            setSearchQuery(searchTerm);
            handleSearch(searchTerm);
          }}
        />
      </SearchProvider>
      {searchResults && <ResultsListView searchResults={searchResults} />}
    </div>
  );
};

export default SearchBar;
