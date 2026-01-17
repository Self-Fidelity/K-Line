import {
    ISeriesPrimitive,
    IPrimitivePaneRenderer,
    IPrimitivePaneView,
    PrimitivePaneViewZOrder,
    IChartApi,
    ISeriesApi,
} from 'lightweight-charts';

interface ChipBin {
    price: number;
    volume: number;
    width?: number; // Calculated pixel width
    color?: string;
}

export interface ChipDistributionData {
    bins: number[];
    chips: number[];
    currentPrice: number;
    date?: string;
}

class ChipDistributionPaneRenderer implements IPrimitivePaneRenderer {
    private _data: ChipDistributionData | null = null;
    private _view: ChipDistributionPaneView;

    constructor(view: ChipDistributionPaneView) {
        this._view = view;
    }

    draw(target: any) {
        // target is CanvasRenderingTarget2D which is a wrapper often in 4.x
        // We need to use useBitmapCoordinateSpace

        target.useBitmapCoordinateSpace((scope: any) => {
            const ctx = scope.context;
            this._drawImpl(ctx, scope);
        });
    }

    private _drawImpl(ctx: CanvasRenderingContext2D, scope: any) {
        const view = this._view;
        const data = view.getData();
        const source = view.getSource();
        const series = source.attachedSeries;

        if (!data || !series || data.bins.length === 0) {
            return;
        }



        // const chartWidth = scope.mediaSize.width;
        const maxBarWidth = scope.mediaSize.width * 0.3;

        // Find max chips for scaling
        const maxChip = Math.max(...data.chips);

        const { bins, chips, currentPrice } = data;

        ctx.save();

        for (let i = 0; i < bins.length; i++) {
            const price = bins[i];
            const vol = chips[i];

            // Scope.verticalPixelRatio might be needed if drawing on bitmap.
            const verticalPixelRatio = scope.verticalPixelRatio;

            let y = series.priceToCoordinate(price) as unknown as number;
            if (y === null) continue;

            // Scale to bitmap
            y *= verticalPixelRatio;

            const step = bins[1] - bins[0];
            let yNext = series.priceToCoordinate(price + step) as unknown as number;

            // Height
            let barHeight = 0;
            if (yNext !== null) {
                yNext *= verticalPixelRatio;
                barHeight = Math.abs(y - yNext);
            } else {
                barHeight = 2 * verticalPixelRatio;
            }

            // Ensure min height
            if (barHeight < 1 * verticalPixelRatio) barHeight = 1 * verticalPixelRatio;

            // Width
            const barWidth = (vol / maxChip) * maxBarWidth * scope.horizontalPixelRatio;

            // Color
            const isProfit = price < currentPrice;
            const color = isProfit ? 'rgba(244, 67, 54, 0.4)' : 'rgba(76, 175, 80, 0.4)';

            ctx.fillStyle = color;

            // Horizontal Bar from Right
            const bitmapWidth = scope.bitmapSize.width;
            const x = bitmapWidth - barWidth;

            // Draw
            const top = (yNext !== null && yNext < y) ? yNext : (y - barHeight);

            ctx.fillRect(x, top, barWidth, barHeight);
        }

        ctx.restore();
    }
}

class ChipDistributionPaneView implements IPrimitivePaneView {
    private _source: ChipDistributionSeries;
    private _data: ChipDistributionData | null = null;

    constructor(source: ChipDistributionSeries) {
        this._source = source;
    }

    update(data: ChipDistributionData) {
        this._data = data;
    }

    getData() {
        return this._data;
    }

    getSource() {
        return this._source;
    }

    renderer() {
        return new ChipDistributionPaneRenderer(this);
    }

    zOrder(): PrimitivePaneViewZOrder {
        return 'normal';
    }
}

export default class ChipDistributionSeries implements ISeriesPrimitive {
    _paneViews: ChipDistributionPaneView[];
    _data: ChipDistributionData | null = null;
    chart: IChartApi | null = null;
    attachedSeries: ISeriesApi<"Candlestick"> | null = null;

    constructor() {
        this._paneViews = [new ChipDistributionPaneView(this)];
    }

    setData(data: ChipDistributionData) {
        this._data = data;
        this._paneViews[0].update(data);
        this.requestUpdate();
    }

    // Use 'any' to bypass strict type check for now
    attached(param: any) {
        this.chart = param.chart;
        this.attachedSeries = param.series;
        // this.requestUpdate = param.requestUpdate; // Use the provided requestUpdate
        // Need to bind requestUpdate if we want to use it
        this._requestUpdateCallback = param.requestUpdate;
    }

    detached() {
        this.chart = null;
        this.attachedSeries = null;
        this._requestUpdateCallback = null;
    }

    // Internal callback holder
    private _requestUpdateCallback: (() => void) | null = null;

    // Override requestUpdate to use the callback
    requestUpdate() {
        if (this._requestUpdateCallback) {
            this._requestUpdateCallback();
        }
    }

    // ISeriesPrimitive interface methods
    paneViews() {
        return this._paneViews;
    }

    axisViews() {
        return [];
    }

    priceAxisPaneViews() {
        return [];
    }

    timeAxisPaneViews() {
        return [];
    }

    autoscaleInfo() {
        return null; // Don't affect autoscaling
    }

    hitTest() {
        return null;
    }
}


