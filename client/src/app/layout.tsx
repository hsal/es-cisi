import { Inter } from 'next/font/google';
import '@/styles/globals.scss';

import { cn } from '@/lib/utils';

import Layout from '../components/global/Layout';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

type RootLayoutPropTypes = {
  children: React.ReactNode;
};

export const metadata = {
  title: 'Ghar',
  description: 'Information Retrieval System',
  icons: {
    icon: '/favicon.ico',
  },
};

const RootLayout = ({ children }: Readonly<RootLayoutPropTypes>) => {
  return (
    <html lang='en'>
      <body
        className={cn(
          'min-h-screen bg-primary font-sans antialiased',
          inter.variable
        )}
      >
        <Layout>{children}</Layout>
      </body>
    </html>
  );
};

export default RootLayout;
