import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Bookmark, Globe, Zap, Search, Clock } from "lucide-react";

export function Dashboard() {
    const stats = [
        { label: 'Total Bookmarks', value: '4,128', change: '+24 this week', icon: Bookmark, color: 'text-blue-500' },
        { label: 'Browsers Linked', value: '3', change: 'Edge, Chrome, Firefox', icon: Globe, color: 'text-green-500' },
        { label: 'Sync Status', value: 'Live', change: 'Last sync: 1m ago', icon: Activity, color: 'text-purple-500' },
        { label: 'Search Index', value: 'Ready', change: '100% Optimized', icon: Zap, color: 'text-yellow-500' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Bookmark Master</h2>
                    <p className="text-slate-400">Browser knowledge base management</p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {stats.map((stat, idx) => (
                    <Card key={idx} className="border-slate-800 bg-slate-950/50">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-200">
                                {stat.label}
                            </CardTitle>
                            <stat.icon className={`h-4 w-4 ${stat.color}`} />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stat.value}</div>
                            <p className="text-xs text-slate-400">
                                {stat.change}
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Recent Additions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-slate-900/40 border border-slate-800">
                                    <div className="p-2 rounded bg-blue-500/10">
                                        <Bookmark className="h-4 w-4 text-blue-500" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-slate-200 truncate">Example Bookmark Title {i}</p>
                                        <p className="text-xs text-slate-500 truncate">https://example.com/page-{i}</p>
                                    </div>
                                    <div className="text-xs text-slate-500">2h ago</div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Frequent Sites</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-xs text-slate-400">
                                    <span>GitHub</span>
                                    <span>428 visits</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-[85%]" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-xs text-slate-400">
                                    <span>StackOverflow</span>
                                    <span>156 visits</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-[45%]" />
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
