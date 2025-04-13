'use client';

import IconLink from '../shared/IconLink';

const NavBar = () => {
  return (
    <header className='bg-white shadow-md relative'>
      <div className='container mx-auto flex justify-between items-center p-4'>
        <IconLink
          src='qmul-logo'
          width={100}
          height={100}
          alt='logo'
          navigateTo='/'
          text='Information Retrieval'
          classes='font-bold'
        />
      </div>
    </header>
  );
};

export default NavBar;
