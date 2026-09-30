import React from "react";

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    /*
      Mobile: compact top/bottom padding so login card isn't cramped.
      Tablet+: generous vertical breathing room.
      The Header is sticky and rendered in the root layout (above this),
      so we only need to provide page content spacing here.
    */
    <div className="min-h-[calc(100vh-5rem)] flex flex-col justify-center py-6 sm:py-12 px-0">
      {children}
    </div>
  );
}
