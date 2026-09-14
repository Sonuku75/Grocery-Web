"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AccountLayout } from "@/components/account/AccountLayout";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { RevokeSessionModal, RevokeMode } from "@/components/account/RevokeSessionModal";
import { accountService } from "@/services/accountService";
import { useToast } from "@/context/ToastContext";
import { UserSession } from "@/types";
import { formatDate } from "@/lib/utils";
import {
  Smartphone,
  Laptop,
  Globe,
  Tablet,
  ShieldCheck,
  ShieldAlert,
  Clock,
  MapPin,
  Trash2,
  LogOut,
  RefreshCw,
  Loader2,
  CheckCircle2,
} from "lucide-react";

export default function AccountSessionsPage() {
  const { showToast } = useToast();

  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Revoke modal state
  const [isRevokeModalOpen, setIsRevokeModalOpen] = useState<boolean>(false);
  const [revokeMode, setRevokeMode] = useState<RevokeMode>("SINGLE");
  const [targetSession, setTargetSession] = useState<UserSession | null>(null);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await accountService.getSessions();
      setSessions(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load active sessions.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleOpenSingleRevoke = (sess: UserSession) => {
    setRevokeMode("SINGLE");
    setTargetSession(sess);
    setIsRevokeModalOpen(true);
  };

  const handleOpenOthersRevoke = () => {
    setRevokeMode("OTHERS");
    setTargetSession(null);
    setIsRevokeModalOpen(true);
  };

  const handleOpenAllRevoke = () => {
    setRevokeMode("ALL");
    setTargetSession(null);
    setIsRevokeModalOpen(true);
  };

  const getDeviceIcon = (platform?: string | null, deviceName?: string | null) => {
    const text = `${platform || ""} ${deviceName || ""}`.toLowerCase();
    if (text.includes("iphone") || text.includes("android") || text.includes("mobile")) {
      return <Smartphone className="w-5 h-5 text-brand-600" />;
    }
    if (text.includes("ipad") || text.includes("tablet")) {
      return <Tablet className="w-5 h-5 text-indigo-600" />;
    }
    if (text.includes("mac") || text.includes("windows") || text.includes("linux") || text.includes("desktop")) {
      return <Laptop className="w-5 h-5 text-slate-700" />;
    }
    return <Globe className="w-5 h-5 text-slate-500" />;
  };

  const otherSessionsCount = sessions.filter((s) => !s.is_current && !s.isCurrent).length;

  return (
    <AccountLayout
      title="Active Device Sessions"
      description="Inspect devices that currently have access to your Cartify account and revoke unauthorized sessions."
      breadcrumbItems={[
        { label: "Security", href: "/account/security" },
        { label: "Active Sessions" },
      ]}
      rightAction={
        <div className="flex items-center gap-2">
          {otherSessionsCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenOthersRevoke}
              leftIcon={<LogOut className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              Sign Out Other Devices
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={loadSessions}
            disabled={isLoading}
            aria-label="Refresh sessions list"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      }
    >
      {/* Privacy Notice Banner */}
      <div className="p-4 rounded-2xl bg-white border border-slate-100 shadow-xs flex items-start gap-3 text-xs text-slate-600">
        <ShieldCheck className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-semibold text-slate-900">Cryptographic Session Protection</p>
          <p className="text-slate-500">
            For your privacy, Cartify stores only cryptographic SHA-256 hashes of session tokens. IP addresses are masked, and raw session tokens are never accessible to anyone.
          </p>
        </div>
      </div>

      {/* Main Sessions List */}
      <section
        aria-label="Active Sessions List"
        className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs space-y-6"
      >
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">Connected Devices</h2>
            <p className="text-xs text-slate-500">
              Showing {sessions.length} active device {sessions.length === 1 ? "session" : "sessions"}.
            </p>
          </div>
          {sessions.length > 1 && (
            <Button
              variant="danger"
              size="sm"
              onClick={handleOpenAllRevoke}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              Sign Out All Everywhere
            </Button>
          )}
        </div>

        {isLoading && sessions.length === 0 ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-6 h-6 text-brand-600 animate-spin" />
            <p className="text-xs text-slate-500">Loading active sessions...</p>
          </div>
        ) : sessions.length === 0 ? (
          <EmptyState
            title="No other active sessions"
            description="You are currently signed in on this device only."
            icon={<Smartphone className="w-8 h-8 text-slate-400" />}
          />
        ) : (
          <div className="divide-y divide-slate-100">
            {sessions.map((sess) => {
              const isCurrent = sess.is_current || sess.isCurrent;
              const deviceName = sess.device_name || sess.deviceName || "Unrecognized Device";
              const platform = sess.platform || "Web Browser";
              const ip = sess.ip_address || sess.ipAddress || "Masked IP";
              const lastActive = sess.last_seen_at || sess.lastSeenAt || sess.created_at || sess.createdAt;

              return (
                <div
                  key={sess.id}
                  className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-11 h-11 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0 mt-0.5">
                      {getDeviceIcon(platform, deviceName)}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-900">{deviceName}</h3>
                        {isCurrent ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                            <CheckCircle2 className="w-3 h-3" />
                            This Device
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">
                            Active
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                        <span>{platform}</span>
                        <span>•</span>
                        <span className="font-mono text-[11px]">{ip}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          Last active: {formatDate(lastActive || new Date().toISOString())}
                        </span>
                      </div>
                    </div>
                  </div>

                  {!isCurrent && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenSingleRevoke(sess)}
                      leftIcon={<LogOut className="w-3.5 h-3.5" />}
                      className="shrink-0 self-end sm:self-center text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 hover:border-rose-200"
                    >
                      Sign Out Device
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Revoke Confirmation Modal */}
      <RevokeSessionModal
        isOpen={isRevokeModalOpen}
        onClose={() => setIsRevokeModalOpen(false)}
        mode={revokeMode}
        targetSession={targetSession}
        onRevocationComplete={loadSessions}
      />
    </AccountLayout>
  );
}
