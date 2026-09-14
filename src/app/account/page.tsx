"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { AccountLayout } from "@/components/account/AccountLayout";
import { ProfileEditModal } from "@/components/account/ProfileEditModal";
import { EmailChangeModal } from "@/components/account/EmailChangeModal";
import { PhoneChangeModal } from "@/components/account/PhoneChangeModal";
import { DeleteAccountModal } from "@/components/account/DeleteAccountModal";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { accountService } from "@/services/accountService";
import { orderService } from "@/services/orderService";
import { addressService } from "@/services/addressService";
import { wishlistService } from "@/services/wishlistService";
import { notificationService } from "@/services/notificationService";
import {
  AccountProfile,
  AccountSecuritySummary,
  Address,
  Order,
  Product,
} from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  User,
  Mail,
  Phone,
  Calendar,
  Edit2,
  PackageCheck,
  MapPin,
  Heart,
  Bell,
  ShieldCheck,
  Smartphone,
  AlertTriangle,
  ChevronRight,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Loader2,
  Clock,
  Trash2,
  Undo2,
} from "lucide-react";

export default function AccountDashboardPage() {
  const { user } = useAuth();
  const { showToast } = useToast();

  // Data states
  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [securitySummary, setSecuritySummary] = useState<AccountSecuritySummary | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [wishlistCount, setWishlistCount] = useState<number>(0);
  const [unreadNotifications, setUnreadNotifications] = useState<number>(0);

  // Loading & error states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasError, setHasError] = useState<boolean>(false);
  const [isCancellingDeletion, setIsCancellingDeletion] = useState<boolean>(false);

  // Modals
  const [isEditProfileOpen, setIsEditProfileOpen] = useState<boolean>(false);
  const [isEmailChangeOpen, setIsEmailChangeOpen] = useState<boolean>(false);
  const [isPhoneChangeOpen, setIsPhoneChangeOpen] = useState<boolean>(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);

  const loadAccountData = useCallback(async () => {
    setIsLoading(true);
    setHasError(false);

    try {
      const [
        profileData,
        securityData,
        ordersData,
        addressData,
        wishlistData,
        unreadCount,
      ] = await Promise.allSettled([
        accountService.getAccountOverview(),
        accountService.getSecuritySummary(),
        orderService.getOrders({ limit: 3 }),
        addressService.getAddresses(),
        wishlistService.getWishlist(undefined, 1),
        notificationService.getUnreadCount(),
      ]);

      if (profileData.status === "fulfilled") {
        setProfile(profileData.value);
      } else {
        console.error("Failed to load profile:", profileData.reason);
      }

      if (securityData.status === "fulfilled") {
        setSecuritySummary(securityData.value);
      }

      if (ordersData.status === "fulfilled") {
        setRecentOrders(ordersData.value.slice(0, 3));
      }

      if (addressData.status === "fulfilled") {
        setAddresses(addressData.value);
      }

      if (wishlistData.status === "fulfilled") {
        setWishlistCount(wishlistData.value.count);
      }

      if (unreadCount.status === "fulfilled") {
        setUnreadNotifications(unreadCount.value);
      }

      if (profileData.status === "rejected") {
        setHasError(true);
      }
    } catch (err) {
      console.error("Critical account overview load failure:", err);
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccountData();
  }, [loadAccountData]);

  const handleCancelDeletion = async () => {
    setIsCancellingDeletion(true);
    try {
      const res = await accountService.cancelDeletion();
      showToast(res.message || "Account deletion request cancelled successfully.", "success");
      if (profile) {
        setProfile({ ...profile, has_pending_deletion: false });
      }
      if (securitySummary) {
        setSecuritySummary({ ...securitySummary, has_pending_deletion: false });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to cancel account deletion.";
      showToast(msg, "error");
    } finally {
      setIsCancellingDeletion(false);
    }
  };

  const getOrderStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case "DELIVERED":
        return <Badge variant="success">Delivered</Badge>;
      case "SHIPPED":
      case "OUT_FOR_DELIVERY":
        return <Badge variant="brand">In Transit</Badge>;
      case "CONFIRMED":
      case "PROCESSING":
        return <Badge variant="warning">Processing</Badge>;
      case "CANCELLED":
        return <Badge variant="danger">Cancelled</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  if (hasError && !profile) {
    return (
      <AccountLayout
        title="Account Dashboard"
        description="Manage your profile, security, and preferences."
      >
        <div className="bg-white rounded-3xl border border-slate-100 p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-slate-900">Unable to load your account</h2>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              We encountered an issue retrieving your account details. Please verify your internet connection or try again.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAccountData}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Retry
          </Button>
        </div>
      </AccountLayout>
    );
  }

  return (
    <AccountLayout
      title="Account Dashboard"
      description="View and manage your personal profile, security credentials, orders, and addresses."
    >
      {/* 1. Pending Deletion Warning Banner */}
      {profile?.has_pending_deletion && (
        <section
          aria-label="Pending Account Deletion Notice"
          className="p-5 sm:p-6 rounded-3xl bg-rose-50 border border-rose-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fade-in"
        >
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-rose-900">Account Scheduled for Deletion</h2>
                <Badge variant="danger">Pending 30-Day Grace</Badge>
              </div>
              <p className="text-xs text-rose-700 max-w-xl leading-relaxed">
                Your deletion request is currently in the 30-day grace period. During this time, you can cancel the request to keep full access to your account and purchase history.
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="danger"
            size="sm"
            isLoading={isCancellingDeletion}
            onClick={handleCancelDeletion}
            leftIcon={<Undo2 className="w-3.5 h-3.5" />}
            className="shrink-0 self-start sm:self-center"
          >
            Cancel Deletion
          </Button>
        </section>
      )}

      {/* 2. Customer Profile Card */}
      <section
        aria-label="Personal Profile Summary"
        className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs relative overflow-hidden"
      >
        {isLoading && !profile ? (
          <div className="space-y-4 animate-pulse">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-slate-200" />
              <div className="space-y-2">
                <div className="h-5 w-40 bg-slate-200 rounded-md" />
                <div className="h-4 w-60 bg-slate-100 rounded-md" />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            {/* Left: Avatar + Details */}
            <div className="flex items-start sm:items-center gap-4 sm:gap-6">
              <div className="relative w-16 h-16 sm:w-20 sm:h-20 rounded-2xl sm:rounded-3xl overflow-hidden bg-brand-100 border-2 border-brand-200/60 shrink-0 flex items-center justify-center text-brand-700 shadow-xs">
                {profile?.avatar_url || profile?.avatarUrl ? (
                  <Image
                    src={profile.avatar_url || profile.avatarUrl || ""}
                    alt={profile?.name || "Avatar"}
                    fill
                    sizes="80px"
                    className="object-cover"
                  />
                ) : (
                  <User className="w-8 h-8 sm:w-10 sm:h-10 text-brand-600" />
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg sm:text-xl font-black text-slate-900">
                    {profile?.name || user?.fullName || "Valued Customer"}
                  </h2>
                  {profile?.is_verified ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                      <ShieldCheck className="w-3 h-3" />
                      Verified
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600">
                      Unverified
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    <span>{profile?.email || user?.email}</span>
                  </div>
                  {profile?.phone && (
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{profile.phone}</span>
                    </div>
                  )}
                </div>

                {profile?.bio && (
                  <p className="text-xs text-slate-600 max-w-lg italic pt-1">
                    &ldquo;{profile.bio}&rdquo;
                  </p>
                )}
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-2 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditProfileOpen(true)}
                leftIcon={<Edit2 className="w-3.5 h-3.5" />}
              >
                Edit Profile
              </Button>
            </div>
          </div>
        )}
      </section>

      {/* 3. Quick Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Orders Count */}
        <Link
          href="/orders"
          className="group p-4 sm:p-5 rounded-2xl bg-white border border-slate-100 shadow-xs hover:border-brand-200 hover:shadow-card transition-all flex flex-col justify-between"
        >
          <div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <PackageCheck className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Total Orders</p>
            <p className="text-xl sm:text-2xl font-black text-slate-900">
              {recentOrders.length > 0 ? recentOrders.length : "0"}
            </p>
          </div>
        </Link>

        {/* Saved Addresses */}
        <Link
          href="/addresses"
          className="group p-4 sm:p-5 rounded-2xl bg-white border border-slate-100 shadow-xs hover:border-indigo-200 hover:shadow-card transition-all flex flex-col justify-between"
        >
          <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Saved Addresses</p>
            <p className="text-xl sm:text-2xl font-black text-slate-900">
              {addresses.length}
            </p>
          </div>
        </Link>

        {/* Wishlist Items */}
        <Link
          href="/wishlist"
          className="group p-4 sm:p-5 rounded-2xl bg-white border border-slate-100 shadow-xs hover:border-rose-200 hover:shadow-card transition-all flex flex-col justify-between"
        >
          <div className="w-9 h-9 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <Heart className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Wishlist Items</p>
            <p className="text-xl sm:text-2xl font-black text-slate-900">
              {wishlistCount}
            </p>
          </div>
        </Link>

        {/* Unread Notifications */}
        <Link
          href="/account/notifications"
          className="group p-4 sm:p-5 rounded-2xl bg-white border border-slate-100 shadow-xs hover:border-amber-200 hover:shadow-card transition-all flex flex-col justify-between"
        >
          <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <Bell className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Unread Alerts</p>
            <p className="text-xl sm:text-2xl font-black text-slate-900">
              {unreadNotifications}
            </p>
          </div>
        </Link>
      </div>

      {/* 4. Recent Orders Section */}
      <section
        aria-label="Recent Orders"
        className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs space-y-5"
      >
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-base sm:text-lg font-bold text-slate-900">Recent Orders</h2>
            <p className="text-xs text-slate-500">Track and manage your most recent purchases.</p>
          </div>
          <Link
            href="/orders"
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 group"
          >
            <span>View All</span>
            <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>

        {recentOrders.length === 0 ? (
          <EmptyState
            title="No orders placed yet"
            description="When you purchase fresh groceries and pantry essentials, your orders will appear here."
            actionText="Start Shopping"
            actionHref="/products"
            icon={<PackageCheck className="w-8 h-8 text-slate-400" />}
          />
        ) : (
          <div className="divide-y divide-slate-100">
            {recentOrders.map((order) => (
              <div
                key={order.id}
                className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0">
                    <PackageCheck className="w-5 h-5 text-brand-600" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900">
                        #{order.orderNumber || order.id.slice(0, 8)}
                      </span>
                      {getOrderStatusBadge(order.status)}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>{formatDate(order.createdAt)}</span>
                      <span>•</span>
                      <span>{order.items?.length || 1} items</span>
                      <span>•</span>
                      <span className="font-bold text-slate-900">
                        {formatCurrency(order.totalAmount || order.total || 0)}
                      </span>
                    </div>
                  </div>
                </div>

                <Link
                  href={`/orders/${order.id}`}
                  className="self-end sm:self-center text-xs font-semibold text-slate-700 hover:text-brand-600 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-brand-300 transition-colors"
                >
                  <span>Order Details</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 5. Addresses & Security Overview (Two Column Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Saved Addresses Card */}
        <section
          aria-label="Delivery Addresses"
          className="bg-white rounded-3xl border border-slate-100 p-6 shadow-xs flex flex-col justify-between space-y-4"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <MapPin className="w-4 h-4" />
                </div>
                <h2 className="text-base font-bold text-slate-900">Delivery Addresses</h2>
              </div>
              <Badge variant="neutral">{addresses.length} saved</Badge>
            </div>

            {addresses.length === 0 ? (
              <p className="text-xs text-slate-500 leading-relaxed">
                You haven&apos;t saved any delivery addresses yet. Add home, work, or other addresses for faster checkout.
              </p>
            ) : (
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 space-y-1 text-xs">
                <div className="flex items-center gap-2 font-bold text-slate-900">
                  <span>{addresses[0].recipientName || addresses[0].recipient_name || "Primary Address"}</span>
                  {addresses[0].isDefault && <Badge variant="success">Default</Badge>}
                </div>
                <p className="text-slate-600 truncate">
                  {addresses[0].addressLine1 || addresses[0].houseFlat}, {addresses[0].city}
                </p>
                <p className="text-slate-400 text-[11px]">
                  PIN: {addresses[0].postalCode || addresses[0].pincode}
                </p>
              </div>
            )}
          </div>

          <Link href="/addresses" className="w-full">
            <Button variant="outline" size="sm" fullWidth>
              Manage Saved Addresses
            </Button>
          </Link>
        </section>

        {/* Security & Sessions Card */}
        <section
          aria-label="Security & Authentication"
          className="bg-white rounded-3xl border border-slate-100 p-6 shadow-xs flex flex-col justify-between space-y-4"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <h2 className="text-base font-bold text-slate-900">Account Security</h2>
              </div>
              <Badge variant="success">Protected</Badge>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Email Status</span>
                <span className="font-semibold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verified
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Active Device Sessions</span>
                <span className="font-semibold text-slate-900">
                  {securitySummary?.active_sessions || 1} device(s)
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500">Password Status</span>
                <span className="font-semibold text-slate-700">Up to date</span>
              </div>
            </div>
          </div>

          <Link href="/account/security" className="w-full">
            <Button variant="outline" size="sm" fullWidth>
              Security Settings & Sessions
            </Button>
          </Link>
        </section>
      </div>

      {/* 6. Danger Zone */}
      <section
        aria-label="Account Danger Zone"
        className="bg-white rounded-3xl border border-rose-100 p-6 sm:p-8 shadow-xs space-y-4"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-rose-900">Danger Zone</h2>
            <p className="text-xs text-slate-500">
              Irreversible and scheduled lifecycle actions for your customer account.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-rose-50/50 border border-rose-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-900">Delete Customer Account</p>
            <p className="text-xs text-slate-500 max-w-xl">
              Permanently schedule your account for deactivation with a 30-day grace period. Historical transaction records will be retained in accordance with tax and legal requirements.
            </p>
          </div>
          {profile?.has_pending_deletion ? (
            <Button
              variant="outline"
              size="sm"
              isLoading={isCancellingDeletion}
              onClick={handleCancelDeletion}
              className="shrink-0 text-xs"
            >
              Cancel Deletion Request
            </Button>
          ) : (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setIsDeleteModalOpen(true)}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
              className="shrink-0 text-xs"
            >
              Delete Account
            </Button>
          )}
        </div>
      </section>

      {/* Modals */}
      <ProfileEditModal
        isOpen={isEditProfileOpen}
        onClose={() => setIsEditProfileOpen(false)}
        profile={profile}
        onProfileUpdated={(updated) => setProfile(updated)}
        onOpenEmailChange={() => setIsEmailChangeOpen(true)}
      />

      <EmailChangeModal
        isOpen={isEmailChangeOpen}
        onClose={() => setIsEmailChangeOpen(false)}
        currentEmail={profile?.email || user?.email || ""}
        onEmailUpdated={(updated) => setProfile(updated)}
      />

      <PhoneChangeModal
        isOpen={isPhoneChangeOpen}
        onClose={() => setIsPhoneChangeOpen(false)}
        currentPhone={profile?.phone}
        onPhoneUpdated={(updated) => setProfile(updated)}
      />

      <DeleteAccountModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onDeletionScheduled={(res) => {
          if (profile) setProfile({ ...profile, has_pending_deletion: true });
        }}
      />
    </AccountLayout>
  );
}
