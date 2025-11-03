"use client";

import React, { useState, useEffect, useRef } from "react";
import { Video, Menu, X, User, LogOut, Settings, Search } from "lucide-react";
import Link from "next/link";
import Image from "next/image"
import { usePathname, useRouter } from "next/navigation";

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const pathname = usePathname();
  const router = useRouter();
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check if we're on a stream page
  const isStreamPage = pathname.startsWith('/stream/');

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // You can implement search functionality here
      console.log("Searching for:", searchQuery);
      // For example: router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleGoLive = () => {
    router.push('/stream/1');
  };

  return (
    <nav className="fixed top-0 left-0 w-full bg-[#1a202c2d] backdrop-blur-md border-b border-[#4A5568]/30 z-50 shadow-lg">
      <div className="mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        {/* Logo + Name */}
        <Link href="/" className="flex items-center space-x-2">
          <Image src="/logo_nav.png" height={20} width={20} className=" sm:h-8 sm:w-8 text-[#2B6CB0]" alt={""} />
          <span className="text-lg sm:text-xl font-bold text-[#FFFFFF]">
            The Miasma Filter
          </span>
        </Link>

        {/* Search Bar - Only show when NOT on stream page */}
        {!isStreamPage && (
          <div className="hidden md:flex flex-1 max-w-2xl mx-8 opacity-70">
            <form onSubmit={handleSearchSubmit} className="w-full relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[#9CA3AF]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search news, topics, streams..."
                  className="w-full pl-10 pr-4 py-2 bg-[#2D3748] border border-[#4A5568] rounded-lg text-[#E2E8F0] placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#2B6CB0] focus:border-transparent transition-all"
                />
              </div>
            </form>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* Go Live Button - Only show when NOT on stream page */}
          {!isStreamPage && (
            <button
              onClick={handleGoLive}
              className="px-3 sm:px-4 py-2 rounded-lg bg-[#DC2626] text-white font-medium text-sm sm:text-base transition-all hover:bg-[#B91C1C] hover:shadow-lg hover:shadow-[#DC2626]/30"
            >
              <span className="hidden sm:inline">🔴 Go Live</span>
              <span className="sm:hidden">Live</span>
            </button>
          )}

          {/* Avatar with Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="w-8 h-8 sm:w-9 sm:h-9 bg-[#2D3748] border border-[#4A5568] rounded-full flex items-center justify-center cursor-pointer hover:border-[#9CA3AF] focus:ring-2 focus:ring-[#2B6CB0] transition"
            >
              <User className="h-4 w-4 text-[#E2E8F0]" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-44 bg-[#1A202C] border border-[#4A5568] rounded-lg shadow-lg py-2 animate-fadeIn z-50">
                <Link
                  href="/profile"
                  className="block px-4 py-2 text-[#9CA3AF] hover:bg-[#2D3748] hover:text-[#E2E8F0] transition"
                >
                  Profile
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center px-4 py-2 text-[#9CA3AF] hover:bg-[#2D3748] hover:text-[#E2E8F0] transition"
                >
                  <Settings className="h-4 w-4 mr-2" /> Settings
                </Link>
                <button className="flex items-center w-full px-4 py-2 text-[#9CA3AF] hover:bg-[#2D3748] hover:text-[#E2E8F0] transition">
                  <LogOut className="h-4 w-4 mr-2" /> Logout
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button - Only show when NOT on stream page */}
          {!isStreamPage && (
            <button
              className="md:hidden text-[#9CA3AF] hover:text-[#E2E8F0] transition"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          )}
        </div>
      </div>

      {/* Mobile Menu - Only show when NOT on stream page */}
      {!isStreamPage && mobileOpen && (
        <div className="md:hidden bg-[#1A202C]/95 border-t border-[#4A5568]/30 px-4 py-4 space-y-4 animate-slideDown">
          {/* Mobile Search */}
          <form onSubmit={handleSearchSubmit} className="w-full">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[#9CA3AF]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search news, topics, streams..."
                className="w-full pl-10 pr-4 py-2 bg-[#2D3748] border border-[#4A5568] rounded-lg text-[#E2E8F0] placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#2B6CB0] focus:border-transparent transition-all"
              />
            </div>
          </form>

          {/* Mobile Go Live Button */}
          <button
            onClick={handleGoLive}
            className="w-full px-4 py-2 rounded-lg bg-[#DC2626] text-white font-medium text-sm transition-all hover:bg-[#B91C1C]"
          >
            🔴 Go Live
          </button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
