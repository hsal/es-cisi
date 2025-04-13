import Link from 'next/link';
import React from 'react';
import IconButton from './IconButton';

type IconLinkPropTypes = {
  src: string;
  width: number;
  height: number;
  alt: string;
  navigateTo: string;
  text?: string;
  onClick?: () => void;
  classes?: string;
};

const IconLink: React.FC<IconLinkPropTypes> = ({
  src,
  width,
  height,
  alt,
  text,
  navigateTo,
  onClick,
  classes,
}) => {
  return (
    <div>
      <Link href={navigateTo} className={classes}>
        <IconButton
          src={src}
          width={width}
          height={height}
          alt={alt}
          text={text}
          onClick={onClick}
        />
      </Link>
    </div>
  );
};

export default IconLink;
