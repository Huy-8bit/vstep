"use client";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";
export const Tabs = TabsPrimitive.Root;
export function TabsList({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      className={cn(
        "flex gap-1 overflow-x-auto border-b border-stone-200",
        className,
      )}
      {...props}
    />
  );
}
export function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "relative shrink-0 whitespace-nowrap px-4 py-3 text-sm font-medium text-stone-500 outline-none transition-colors",
        "hover:text-stone-800 focus-visible:ring-2 focus-visible:ring-teal-600",
        "data-[state=active]:text-teal-900",
        "after:absolute after:inset-x-3 after:-bottom-px after:h-0.5 after:rounded-full after:bg-teal-700 after:opacity-0 after:transition-opacity after:duration-200 data-[state=active]:after:opacity-100",
        className,
      )}
      {...props}
    />
  );
}
export function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      className={cn("animate-fade-in mt-6 outline-none", className)}
      {...props}
    />
  );
}
