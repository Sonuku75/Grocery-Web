"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShoppingBag,
  Search,
  MapPin,
  Heart,
  User as UserIcon,
  Menu,
  X,
  ChevronDown,
  Sparkles,
  Tag,
  PackageCheck,
  Compass,
  LogOut,
  MapPinned,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
import { useAuth } from "@/context/AuthContext";
import { useLocation } from "@/context/LocationContext";
import { MOCK_CATEGORIES, MOCK_PRODUCTS } from "@/lib/mockData";
import { Category, SearchSuggestion } from "@/types";
import { categoryService } from "@/services/categoryService";
import { searchService } from "@/services/searchService";
import { cn, formatCurrency } from "@/lib/utils";

export function Header() {
  const router = useRouter();
  const { cart, setIsCartDrawerOpen } = useCart();
  const { wishlistIds } = useWishlist();
  const { user, isAuthenticated, logout } = useAuth();
  const { location, setIsLocationModalOpen } = useLocation();

  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [isMobileSearchOpen, setIsMobileSearchOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [isCategoriesDropdownOpen, setIsCategoriesDropdownOpen] = useState(false);
  const [isMobileCategoriesOpen, setIsMobileCategoriesOpen] = useState(false);
  const [navCategories, setNavCategories] = useState<Category[]>([]);

  const searchRef = useRef<HTMLDivElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const categoriesDropdownRef = useRef<HTMLDivElement>(null);
  const mobileSearchInputRef = useRef<HTMLInputElement>(null);

  // Load active categories for navigation
  useEffect(() => {
    categoryService
      .getCategories(true)
      .then((cats) => {
        setNavCategories(cats.slice(0, 8));
      })
      .catch(() => {});
  }, []);

  // Debounced search suggestion loading (300ms)
  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setSuggestions([]);
      setIsLoadingSuggestions(false);
      setSelectedSuggestionIndex(-1);
      return;
    }

    setIsLoadingSuggestions(true);
    const timer = setTimeout(async () => {
      try {
        const res = await searchService.getSuggestions(trimmed, 8);
        setSuggestions(res.items || []);
      } catch (err) {
        setSuggestions([]);
      } finally {
        setIsLoadingSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Autofocus mobile search input when mobile search drawer opens
  useEffect(() => {
    if (isMobileSearchOpen) {
      setTimeout(() => {
        mobileSearchInputRef.current?.focus();
      }, 50);
    }
  }, [isMobileSearchOpen]);

  // Close search suggestions and dropdowns on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchFocused(false);
      }
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target as Node)) {
        setIsUserDropdownOpen(false);
      }
      if (categoriesDropdownRef.current && !categoriesDropdownRef.current.contains(event.target as Node)) {
        setIsCategoriesDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearchFocused(false);
    setIsMobileSearchOpen(false);
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      router.push("/search");
    }
  };

  const handleSelectSuggestion = (item: SearchSuggestion) => {
    setIsSearchFocused(false);
    setIsMobileSearchOpen(false);
    setSelectedSuggestionIndex(-1);
    if (item.type === "product") {
      router.push(`/products/${item.slug || item.id}`);
    } else if (item.type === "brand") {
      router.push(`/search?q=${encodeURIComponent(item.label)}&brand=${encodeURIComponent(item.label)}`);
    } else if (item.type === "category") {
      router.push(`/categories/${item.slug || item.id}`);
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (!isSearchFocused && !isMobileSearchOpen) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedSuggestionIndex((prev) =>
        prev < suggestions.length - 1 ? prev + 1 : 0
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedSuggestionIndex((prev) =>
        prev > 0 ? prev - 1 : suggestions.length - 1
      );
    } else if (e.key === "Escape") {
      setIsSearchFocused(false);
      setIsMobileSearchOpen(false);
      setSelectedSuggestionIndex(-1);
    } else if (
      e.key === "Enter" &&
      selectedSuggestionIndex >= 0 &&
      selectedSuggestionIndex < suggestions.length
    ) {
      e.preventDefault();
      handleSelectSuggestion(suggestions[selectedSuggestionIndex]);
    }
  };

  const handleAccountClick = () => {
    if (!isAuthenticated) {
      router.push("/login");
    } else {
      setIsUserDropdownOpen(!isUserDropdownOpen);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-xs">
      {/* Top micro announcement bar */}
      <div className="bg-brand-900 text-brand-50 text-[11px] font-medium py-1.5 px-4 hidden sm:block">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-brand-800 text-brand-200 px-2 py-0.5 rounded-full text-[10px] font-semibold">
              ⚡ 15-MIN EXPRESS
            </span>
            <span>Delivery available in San Francisco & Bay Area</span>
          </div>
          <div className="flex items-center gap-4 text-brand-200">
            <Link href="/offers" className="hover:text-white transition-colors">
              Special Deals
            </Link>
            <span className="text-brand-700">•</span>
            <Link href="/faq" className="hover:text-white transition-colors">
              Help & FAQ
            </Link>
          </div>
        </div>
      </div>

      {/* Main Header Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20 gap-3 md:gap-6">
          {/* Brand Logo & Location */}
          <div className="flex items-center gap-3 lg:gap-6">
            {/* Mobile menu hamburger toggle */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100"
              aria-label="Toggle navigation menu"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-brand-600 flex items-center justify-center text-white shadow-md group-hover:bg-brand-700 transition-colors">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl md:text-2xl font-black tracking-tight text-slate-900">
                  Cart<span className="text-brand-600">ify</span>
                </span>
                <span className="text-[9px] font-bold text-slate-400 -mt-1 tracking-wider uppercase hidden sm:block">
                  Fresh & Fast
                </span>
              </div>
            </Link>

            {/* Location Selector Button */}
            <button
              onClick={() => setIsLocationModalOpen(true)}
              className="hidden sm:flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all text-left"
            >
              <div className="w-7 h-7 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                <MapPin className="w-4 h-4" />
              </div>
              <div className="flex flex-col leading-tight">
                <span className="text-[11px] font-bold text-slate-900 flex items-center gap-1">
                  {location.area}
                  <ChevronDown className="w-3 h-3 text-slate-400" />
                </span>
                <span className="text-[10px] text-brand-600 font-semibold">
                  ⚡ in {location.estimatedDeliveryTime}
                </span>
              </div>
            </button>
          </div>

          {/* Search Bar with live autocomplete */}
          <div ref={searchRef} className="flex-1 max-w-xl relative hidden md:block">
            <form onSubmit={handleSearchSubmit} className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Search for organic milk, fresh avocados, sourdough..."
                className="w-full h-11 pl-11 pr-24 rounded-2xl bg-slate-100/80 border border-slate-200/80 text-sm text-slate-800 placeholder:text-slate-400 focus:bg-white focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10 focus:outline-none transition-all shadow-xs"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              {isLoadingSuggestions && (
                <Loader2 className="w-4 h-4 text-brand-600 animate-spin absolute right-24 top-1/2 -translate-y-1/2" />
              )}
              <button
                type="submit"
                className="absolute right-1.5 top-1.5 bottom-1.5 px-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold transition-colors flex items-center gap-1"
              >
                Search
              </button>
            </form>

            {/* Suggestions Overlay */}
            {isSearchFocused && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-dropdown border border-slate-100 p-3 z-50 animate-fade-in">
                {searchQuery.trim().length > 0 ? (
                  <div>
                    {isLoadingSuggestions && suggestions.length === 0 ? (
                      <div className="flex items-center gap-2 p-3 text-xs text-slate-400">
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-600" />
                        <span>Searching catalog...</span>
                      </div>
                    ) : suggestions.length > 0 ? (
                      <div className="space-y-1 max-h-80 overflow-y-auto">
                        {suggestions.map((item, idx) => (
                          <button
                            key={`${item.type}-${item.label}-${idx}`}
                            onClick={() => handleSelectSuggestion(item)}
                            className={cn(
                              "w-full flex items-center justify-between p-2 rounded-xl text-left transition-colors",
                              selectedSuggestionIndex === idx
                                ? "bg-brand-50 text-brand-900"
                                : "hover:bg-slate-50 text-slate-700"
                            )}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              {item.type === "product" && (
                                <div className="w-7 h-7 rounded-lg bg-slate-100 shrink-0 overflow-hidden flex items-center justify-center">
                                  {item.imageUrl ? (
                                    <img
                                      src={item.imageUrl}
                                      alt={item.label}
                                      className="w-full h-full object-cover"
                                    />
                                  ) : (
                                    <Search className="w-3.5 h-3.5 text-slate-400" />
                                  )}
                                </div>
                              )}
                              {item.type === "brand" && (
                                <div className="w-7 h-7 rounded-lg bg-accent-50 text-accent-600 shrink-0 flex items-center justify-center">
                                  <Tag className="w-3.5 h-3.5" />
                                </div>
                              )}
                              {item.type === "category" && (
                                <div className="w-7 h-7 rounded-lg bg-brand-50 text-brand-600 shrink-0 flex items-center justify-center">
                                  <Compass className="w-3.5 h-3.5" />
                                </div>
                              )}
                              <span className="text-sm font-medium truncate">
                                {item.label}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 shrink-0 ml-2">
                              {item.type === "product" && item.price !== undefined && (
                                <span className="text-xs font-semibold text-brand-600">
                                  {formatCurrency(item.price)}
                                </span>
                              )}
                              {item.type === "brand" && (
                                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                                  Brand
                                </span>
                              )}
                              {item.type === "category" && (
                                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-50 text-brand-600">
                                  Category
                                </span>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 p-2">
                        No immediate suggestions for &ldquo;{searchQuery}&rdquo;. Press Enter to search full catalog.
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1 flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-accent-500" /> Trending Searches
                    </p>
                    <div className="flex flex-wrap gap-1.5 p-1 mt-1">
                      {["Organic Avocados", "Whole Milk", "Brown Eggs", "Sourdough", "Olive Oil", "Strawberries"].map((trend) => (
                        <button
                          key={trend}
                          onClick={() => {
                            setSearchQuery(trend);
                            router.push(`/search?q=${encodeURIComponent(trend)}`);
                            setIsSearchFocused(false);
                          }}
                          className="text-xs font-medium bg-slate-100 hover:bg-brand-50 hover:text-brand-700 px-2.5 py-1.5 rounded-lg text-slate-600 transition-colors"
                        >
                          {trend}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Links & User Dropdown */}
          <div className="flex items-center gap-1.5 sm:gap-2 md:gap-3 shrink-0">
            {/* Categories link and dropdown on desktop & laptop */}
            <div ref={categoriesDropdownRef} className="relative hidden lg:block">
              <button
                onClick={() => setIsCategoriesDropdownOpen(!isCategoriesDropdownOpen)}
                onMouseEnter={() => setIsCategoriesDropdownOpen(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-brand-600 transition-colors"
                aria-label="Browse categories menu"
              >
                <Compass className="w-4 h-4 text-brand-600" />
                <span>Categories</span>
                <ChevronDown
                  className={cn(
                    "w-3 h-3 text-slate-400 transition-transform duration-200",
                    isCategoriesDropdownOpen && "rotate-180"
                  )}
                />
              </button>

              {isCategoriesDropdownOpen && (
                <div
                  onMouseLeave={() => setIsCategoriesDropdownOpen(false)}
                  className="absolute left-0 top-full mt-1.5 w-72 bg-white rounded-2xl shadow-dropdown border border-slate-100 p-2 z-50 animate-fade-in"
                >
                  <div className="p-2 border-b border-slate-100 mb-1 flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Popular Departments
                    </span>
                    <Link
                      href="/categories"
                      onClick={() => setIsCategoriesDropdownOpen(false)}
                      className="text-[11px] font-bold text-brand-600 hover:text-brand-700"
                    >
                      View All →
                    </Link>
                  </div>
                  <div className="max-h-80 overflow-y-auto space-y-0.5">
                    {navCategories.map((cat) => (
                      <Link
                        key={cat.id}
                        href={`/categories/${cat.slug}`}
                        onClick={() => setIsCategoriesDropdownOpen(false)}
                        className="flex items-center justify-between p-2 rounded-xl text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-brand-600 transition-colors"
                      >
                        <span>{cat.name}</span>
                        {cat.subcategories && cat.subcategories.length > 0 && (
                          <span className="text-[10px] text-slate-400 font-semibold bg-slate-100 px-1.5 py-0.5 rounded-md">
                            {cat.subcategories.length}
                          </span>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Offers Link */}
            <Link
              href="/offers"
              className="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-accent-600 bg-accent-50/70 hover:bg-accent-100 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-accent-500" />
              <span>Offers</span>
            </Link>

            {/* Wishlist Icon */}
            <Link
              href="/wishlist"
              className="relative p-2 sm:p-2.5 rounded-xl text-slate-600 hover:bg-slate-50 hover:text-rose-500 transition-colors"
              aria-label="Wishlist"
            >
              <Heart className="w-5 h-5" />
              {wishlistIds.length > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
                  {wishlistIds.length}
                </span>
              )}
            </Link>

            {/* User Profile / Auth Button & Dropdown */}
            <div ref={userDropdownRef} className="relative">
              <button
                onClick={handleAccountClick}
                className="flex items-center gap-1.5 sm:gap-2 p-1.5 sm:p-2 rounded-xl text-slate-700 hover:bg-slate-50 transition-colors"
                aria-label={isAuthenticated ? "User Account" : "Sign In"}
              >
                <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div className="hidden lg:flex flex-col text-left">
                  <span className="text-xs font-bold text-slate-800 truncate max-w-[100px]">
                    {isAuthenticated && user ? user.fullName.split(" ")[0] : "Account"}
                  </span>
                  <span className="text-[10px] text-slate-400 -mt-0.5">
                    {isAuthenticated ? "My Dashboard" : "Sign In"}
                  </span>
                </div>
                {isAuthenticated && (
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden lg:block" />
                )}
              </button>

              {isAuthenticated && isUserDropdownOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-2xl shadow-dropdown border border-slate-100 p-2 z-50 animate-fade-in">
                  <div className="p-3 border-b border-slate-100 mb-1">
                    <p className="text-xs font-bold text-slate-900">{user?.fullName}</p>
                    <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
                  </div>
                  <Link
                    href="/profile"
                    onClick={() => setIsUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 rounded-xl hover:bg-slate-50"
                  >
                    <UserIcon className="w-4 h-4 text-slate-400" />
                    <span>My Profile</span>
                  </Link>
                  <Link
                    href="/orders"
                    onClick={() => setIsUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 rounded-xl hover:bg-slate-50"
                  >
                    <PackageCheck className="w-4 h-4 text-slate-400" />
                    <span>My Orders</span>
                  </Link>
                  <Link
                    href="/addresses"
                    onClick={() => setIsUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 rounded-xl hover:bg-slate-50"
                  >
                    <MapPinned className="w-4 h-4 text-slate-400" />
                    <span>Saved Addresses</span>
                  </Link>
                  <div className="pt-1 mt-1 border-t border-slate-100">
                    <button
                      onClick={() => {
                        logout();
                        setIsUserDropdownOpen(false);
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-rose-600 rounded-xl hover:bg-rose-50"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Cart Navigation Button */}
            <Link
              href="/cart"
              className="flex items-center gap-2 px-3 sm:px-3.5 py-2 sm:py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-sm hover:shadow transition-all shrink-0"
              aria-label="Shopping Cart"
            >
              <div className="relative">
                <ShoppingBag className="w-4 h-4" />
                {cart.itemCount > 0 && (
                  <span className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-accent-500 text-white text-[10px] font-black flex items-center justify-center ring-2 ring-brand-600">
                    {cart.itemCount}
                  </span>
                )}
              </div>
              <span className="text-xs font-bold hidden sm:inline">
                {formatCurrency(cart.subtotal)}
              </span>
            </Link>
          </div>
        </div>

        {/* Mobile Quick Location Selector Strip (screens < sm) */}
        <div className="sm:hidden pb-2 pt-0.5 flex items-center justify-between text-xs">
          <button
            onClick={() => setIsLocationModalOpen(true)}
            className="flex items-center gap-1.5 text-slate-800 hover:text-brand-600 transition-colors truncate max-w-[78%]"
            aria-label="Change delivery location"
          >
            <MapPin className="w-3.5 h-3.5 text-brand-600 shrink-0" />
            <span className="truncate text-[11px] font-medium">
              Deliver to <strong className="text-slate-900 font-semibold">{location.area}</strong> ({location.pincode})
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
          </button>
          <span className="text-[10px] font-bold text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full shrink-0">
            ⚡ {location.estimatedDeliveryTime}
          </span>
        </div>

        {/* Mobile Search Bar (visible only on phone screen) */}
        <div className="pb-3 md:hidden">
          <div
            onClick={() => setIsMobileSearchOpen(true)}
            className="w-full h-10 pl-9 pr-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-500 flex items-center relative cursor-pointer"
          >
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <span className="truncate">
              {searchQuery ? searchQuery : "Search groceries & essentials..."}
            </span>
          </div>
        </div>
      </div>

      {/* Mobile Hamburger Drawer Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white px-4 py-4 space-y-3 animate-fade-in">
          {/* Mobile location bar */}
          <button
            onClick={() => {
              setIsMobileMenuOpen(false);
              setIsLocationModalOpen(true);
            }}
            className="w-full flex items-center justify-between p-2.5 rounded-xl bg-brand-50 text-brand-800 text-xs font-medium"
          >
            <span className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-brand-600" />
              <span>Deliver to: {location.area} ({location.pincode})</span>
            </span>
            <span className="text-brand-600 font-bold">Change</span>
          </button>

          <div className="space-y-1 text-sm font-semibold text-slate-700">
            <Link
              href="/"
              onClick={() => setIsMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-lg hover:bg-slate-50"
            >
              Home
            </Link>
            <Link
              href="/products"
              onClick={() => setIsMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-lg hover:bg-slate-50"
            >
              All Products
            </Link>
            {/* Mobile Categories Accordion */}
            <div>
              <button
                onClick={() => setIsMobileCategoriesOpen(!isMobileCategoriesOpen)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 text-slate-700 text-sm font-semibold"
              >
                <span>Browse Categories</span>
                <ChevronDown
                  className={cn(
                    "w-4 h-4 text-slate-400 transition-transform duration-200",
                    isMobileCategoriesOpen && "rotate-180"
                  )}
                />
              </button>
              {isMobileCategoriesOpen && (
                <div className="pl-3 pr-1 py-1 space-y-1 text-xs font-medium">
                  {navCategories.map((cat) => (
                    <Link
                      key={cat.id}
                      href={`/categories/${cat.slug}`}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="block px-2 py-1.5 rounded-md text-slate-600 hover:text-brand-600 hover:bg-slate-50"
                    >
                      {cat.name}
                    </Link>
                  ))}
                  <Link
                    href="/categories"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="block px-2 py-1.5 font-bold text-brand-600 hover:text-brand-700"
                  >
                    View All Categories →
                  </Link>
                </div>
              )}
            </div>
            <Link
              href="/offers"
              onClick={() => setIsMobileMenuOpen(false)}
              className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 text-accent-600"
            >
              <span>Offers & Deals</span>
              <Tag className="w-4 h-4" />
            </Link>
            <Link
              href="/cart"
              onClick={() => setIsMobileMenuOpen(false)}
              className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50"
            >
              <span>Shopping Cart</span>
              {cart.itemCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 text-xs font-bold">
                  {cart.itemCount}
                </span>
              )}
            </Link>
            <Link
              href="/wishlist"
              onClick={() => setIsMobileMenuOpen(false)}
              className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50"
            >
              <span>My Wishlist</span>
              {wishlistIds.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 text-xs font-bold">
                  {wishlistIds.length}
                </span>
              )}
            </Link>
            <Link
              href="/orders"
              onClick={() => setIsMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-lg hover:bg-slate-50"
            >
              My Orders
            </Link>
            <Link
              href={isAuthenticated ? "/profile" : "/login"}
              onClick={() => setIsMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-lg hover:bg-slate-50"
            >
              {isAuthenticated ? "Account Settings" : "Sign In / Register"}
            </Link>
          </div>
        </div>
      )}

      {/* Mobile Dedicated Search Full-Width Drawer */}
      {isMobileSearchOpen && (
        <div className="fixed inset-0 z-50 bg-white flex flex-col md:hidden animate-fade-in">
          {/* Header bar */}
          <div className="p-3 border-b border-slate-100 flex items-center gap-2 bg-white">
            <button
              onClick={() => {
                setIsMobileSearchOpen(false);
                setSelectedSuggestionIndex(-1);
              }}
              className="w-10 h-10 flex items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Close search"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>

            <form onSubmit={handleSearchSubmit} className="flex-1 relative">
              <input
                ref={mobileSearchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Search groceries & essentials..."
                className="w-full h-11 pl-10 pr-9 rounded-2xl bg-slate-100 border border-slate-200 text-sm text-slate-800 placeholder:text-slate-400 focus:bg-white focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10 focus:outline-none transition-all"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="w-7 h-7 absolute right-2 top-1/2 -translate-y-1/2 flex items-center justify-center text-slate-400 hover:text-slate-600"
                  aria-label="Clear search query"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </form>
          </div>

          {/* Body suggestions / trending list */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isLoadingSuggestions && suggestions.length === 0 ? (
              <div className="flex items-center justify-center py-12 gap-2 text-sm text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                <span>Searching catalog...</span>
              </div>
            ) : suggestions.length > 0 ? (
              <div className="space-y-1">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1">
                  Suggestions
                </p>
                {suggestions.map((item, idx) => (
                  <button
                    key={`mob-${item.type}-${item.label}-${idx}`}
                    onClick={() => handleSelectSuggestion(item)}
                    className="w-full flex items-center justify-between p-3 rounded-2xl text-left hover:bg-slate-50 active:bg-slate-100 transition-colors border border-transparent hover:border-slate-100"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {item.type === "product" && (
                        <div className="w-9 h-9 rounded-xl bg-slate-100 shrink-0 overflow-hidden flex items-center justify-center">
                          {item.imageUrl ? (
                            <img
                              src={item.imageUrl}
                              alt={item.label}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <Search className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                      )}
                      {item.type === "brand" && (
                        <div className="w-9 h-9 rounded-xl bg-accent-50 text-accent-600 shrink-0 flex items-center justify-center">
                          <Tag className="w-4 h-4" />
                        </div>
                      )}
                      {item.type === "category" && (
                        <div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-600 shrink-0 flex items-center justify-center">
                          <Compass className="w-4 h-4" />
                        </div>
                      )}
                      <span className="text-sm font-medium text-slate-800 truncate">
                        {item.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      {item.type === "product" && item.price !== undefined && (
                        <span className="text-xs font-semibold text-brand-600">
                          {formatCurrency(item.price)}
                        </span>
                      )}
                      {item.type === "brand" && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                          Brand
                        </span>
                      )}
                      {item.type === "category" && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-50 text-brand-600">
                          Category
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : searchQuery.trim() ? (
              <div className="text-center py-12 px-4 text-slate-500">
                <p className="text-sm font-medium mb-1">No instant suggestions</p>
                <p className="text-xs text-slate-400 mb-4">
                  Press Enter to search all departments for &ldquo;{searchQuery}&rdquo;
                </p>
                <button
                  onClick={handleSearchSubmit}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold shadow-sm"
                >
                  Search Catalog
                </button>
              </div>
            ) : (
              <div>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-accent-500" /> Trending Groceries
                </p>
                <div className="flex flex-wrap gap-2 p-1 mt-2">
                  {["Organic Avocados", "Whole Milk", "Brown Eggs", "Sourdough Bread", "Olive Oil", "Strawberries", "Paneer", "Bananas"].map((trend) => (
                    <button
                      key={trend}
                      onClick={() => {
                        setSearchQuery(trend);
                        router.push(`/search?q=${encodeURIComponent(trend)}`);
                        setIsMobileSearchOpen(false);
                      }}
                      className="text-xs font-medium bg-slate-100 hover:bg-brand-50 hover:text-brand-700 px-3.5 py-2 rounded-xl text-slate-700 transition-colors"
                    >
                      {trend}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
