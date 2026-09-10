"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import {
  User,
  PackageCheck,
  MapPin,
  Heart,
  LogOut,
  ShieldCheck,
  Mail,
  Phone,
  Edit2,
  CheckCircle2,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, updateProfile } = useAuth();
  const { showToast } = useToast();

  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.fullName || "Alex Rivera");
  const [mobile, setMobile] = useState(user?.mobile || "+1 (555) 234-5678");
  const [loading, setLoading] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updateProfile({ fullName, mobile });
      setIsEditing(false);
      showToast("Profile details updated successfully!", "success");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    showToast("Logged out successfully", "info");
    router.push("/");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <Breadcrumb items={[{ label: "My Profile" }]} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Sidebar Dashboard Card */}
        <div className="lg:col-span-4 bg-white rounded-3xl border border-slate-100 p-6 shadow-card space-y-6">
          <div className="flex flex-col items-center text-center pb-6 border-b border-slate-100">
            <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-brand-600 to-emerald-400 text-white font-black text-2xl flex items-center justify-center shadow-lg shadow-brand-600/20 mb-3 uppercase">
              {user ? user.fullName.charAt(0) : "A"}
            </div>
            <h2 className="text-lg font-bold text-slate-900">{user?.fullName || "Alex Rivera"}</h2>
            <p className="text-xs text-slate-400">{user?.email || "alex.rivera@cartify.com"}</p>
            <span className="mt-2 text-[10px] font-bold text-brand-700 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Cartify Fresh Club Member
            </span>
          </div>

          <nav className="space-y-1 text-xs font-semibold text-slate-700">
            <Link
              href="/profile"
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-brand-50 text-brand-700 font-bold"
            >
              <User className="w-4 h-4 text-brand-600" />
              <span>Personal Details</span>
            </Link>
            <Link
              href="/orders"
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 transition-colors"
            >
              <PackageCheck className="w-4 h-4 text-slate-400" />
              <span>My Orders & Re-order</span>
            </Link>
            <Link
              href="/addresses"
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 transition-colors"
            >
              <MapPin className="w-4 h-4 text-slate-400" />
              <span>Saved Delivery Addresses</span>
            </Link>
            <Link
              href="/wishlist"
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 transition-colors"
            >
              <Heart className="w-4 h-4 text-slate-400" />
              <span>Wishlist & Saved Items</span>
            </Link>
          </nav>

          <div className="pt-4 border-t border-slate-100">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-bold text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="lg:col-span-8 space-y-6">
          {/* Personal Info Box */}
          <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-card space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">Personal Information</h3>
                <p className="text-xs text-slate-500">Manage your basic customer information</p>
              </div>
              {!isEditing && (
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Edit2 className="w-3.5 h-3.5" />}
                  onClick={() => setIsEditing(true)}
                >
                  Edit Profile
                </Button>
              )}
            </div>

            {isEditing ? (
              <form onSubmit={handleSave} className="space-y-4 max-w-md animate-fade-in">
                <Input
                  label="Full Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
                <Input
                  label="Mobile Number"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  required
                />
                <div className="flex gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" size="sm" isLoading={loading}>
                    Save Changes
                  </Button>
                </div>
              </form>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
                <div>
                  <span className="font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Full Name
                  </span>
                  <p className="text-sm font-semibold text-slate-800">
                    {user?.fullName || "Alex Rivera"}
                  </p>
                </div>
                <div>
                  <span className="font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Email Address
                  </span>
                  <p className="text-sm font-semibold text-slate-800">
                    {user?.email || "alex.rivera@cartify.com"}
                  </p>
                </div>
                <div>
                  <span className="font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Mobile Phone
                  </span>
                  <p className="text-sm font-semibold text-slate-800">
                    {user?.mobile || "+1 (555) 234-5678"}
                  </p>
                </div>
                <div>
                  <span className="font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Account Status
                  </span>
                  <span className="inline-flex items-center gap-1 text-emerald-600 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Verified & Active
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Shortcuts */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link
              href="/orders"
              className="p-5 rounded-2xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover transition-all space-y-1 group"
            >
              <PackageCheck className="w-6 h-6 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                Order History
              </h4>
              <p className="text-xs text-slate-400">Track current or past shipments</p>
            </Link>

            <Link
              href="/addresses"
              className="p-5 rounded-2xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover transition-all space-y-1 group"
            >
              <MapPin className="w-6 h-6 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                Saved Locations
              </h4>
              <p className="text-xs text-slate-400">Manage delivery addresses</p>
            </Link>

            <Link
              href="/wishlist"
              className="p-5 rounded-2xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover transition-all space-y-1 group"
            >
              <Heart className="w-6 h-6 text-rose-500 mb-2" />
              <h4 className="text-sm font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                Saved Favorites
              </h4>
              <p className="text-xs text-slate-400">Quickly add saved goods to cart</p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
