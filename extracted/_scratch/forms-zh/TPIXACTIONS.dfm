object PixActions: TPixActions
  object List: TUiActionList
    object FileFormatAction: TUiAction
      ImageIndex = imgPixFormatEdit
    end
    object DisplayFontIncreaseAction: TUiAction
      MacSecondaryShortCutStr = ''
      MacShortCutStr = ''
      SecondaryShortCutStr = ''
      ShortCutStr = ''
    end
    object DisplayFontDecreaseAction: TUiAction
      MacShortCutStr = ''
      SecondaryShortCutStr = ''
      ShortCutStr = ''
    end
    object DiffToleranceAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'To&lerance Mode'
      GroupIndex = 10
      Hint = 'Tolerance Mode|Detects pixel differences greater than configurable tolerance.'
      ImageIndex = imgPixDiffTolerance
      MacShortCutStr = 'Meta+1'
      ShortCaption = 'Tol'
    end
    object DiffRangeAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Mismatch Ran&ge Mode'
      GroupIndex = 10
      Hint = 'Mismatch Range Mode|Measures degree of pixel difference.'
      ImageIndex = imgPixDiffRange
      MacShortCutStr = 'Meta+2'
      ShortCaption = 'Range'
    end
    object DiffBlendAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Blend Mode'
      GroupIndex = 10
      Hint = 'Blend Mode|Blends pictures based on configurable percentage.'
      ImageIndex = imgPixDiffBlend
      MacShortCutStr = 'Meta+3'
      ShortCaption = 'Blend'
    end
    object AutoScaleAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Auto S&cale'
      Hint = 'Auto Scale|Makes smaller picture as large as other picture.'
      ImageIndex = imgPixAutoScale
      ShortCaption = 'Bigger'
      ToolbarAllowed = False
    end
    object RotateRightAction: TUiAction
      Category = 'View'
      Caption = 'Rotate Cloc&kwise'
      Hint = 'Rotate Clockwise|Spins current picture to right by 90 degrees.'
      ImageIndex = imgPixRotateRight
      ShortCaption = 'CW'
      ToolbarAllowed = False
    end
    object RotateLeftAction: TUiAction
      Category = 'View'
      Caption = 'Rotate Cou&nterclockwise'
      Hint = 'Rotate Counterclockwise|Spins current picture to left by 90 degrees.'
      ImageIndex = imgPixRotateLeft
      ShortCaption = 'CCW'
      ToolbarAllowed = False
    end
    object FlipHorzAction: TUiAction
      Category = 'View'
      Caption = 'Flip &Horizontally'
      Hint = 'Flip Horizontally|Swaps pixels of current picture relative to its horizontal center.'
      ImageIndex = imgPixFlipHorz
      ShortCaption = 'Horz'
      ToolbarAllowed = False
    end
    object FlipVertAction: TUiAction
      Category = 'View'
      Caption = 'Flip &Vertically'
      Hint = 'Flip Vertically|Swaps pixels of current picture relative to its vertical center.'
      ImageIndex = imgPixFlipVert
      ShortCaption = 'Vert'
      ToolbarAllowed = False
    end
    object OffsetResetAction: TUiAction
      Category = 'View'
      Caption = '&Reset Difference Offset'
      Hint = 'Reset Difference Offset|Realigns top left corner of both pictures.'
    end
    object CompareTagsAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Compare &Metadata'
      Hint = 'Compare Metadata|Compares and shows metadata.'
      ImageIndex = imgPixCompareTags
      ShortCaption = 'Meta'
    end
    object BlendToggleAction: TUiAction
      Category = 'View'
      Caption = 'Blend T&oggle'
      Hint = 'Blend Toggle|Switches between left and right pictures.'
      ImageIndex = imgPixBlendToggle
      ShortCutStr = 'F8'
    end
    object FullScreenAction: TUiAction
      Category = 'View'
      Caption = 'Full Scr&een'
      Hint = 'Full Screen|Makes current picture show as large as possible.'
      ImageIndex = imgFullScreen
      ShortCaption = 'Full'
      ShortCutStr = 'F11'
      ToolbarAllowed = False
    end
    object ZoomListAction: TUiAction
      Category = 'View'
      Caption = '&Zoom'
      Hint = 'Zoom|Makes picture appear to change size in picked way.'
    end
    object ZoomInAction: TUiAction
      Category = 'View'
      Caption = 'Zoom &In'
      Hint = 'Zoom In|Makes pictures appear to be larger.'
      ImageIndex = imgZoomIn
      MacSecondaryShortCutStr = 'Meta+='
      MacShortCutStr = 'Meta++'
      SecondaryShortCutStr = 'Ctrl+='
      ShortCutStr = 'Ctrl+Num +'
    end
    object ZoomOutAction: TUiAction
      Category = 'View'
      Caption = 'Zoom &Out'
      Hint = 'Zoom Out|Makes pictures appear to be smaller.'
      ImageIndex = imgZoomOut
      MacShortCutStr = 'Meta+-'
      SecondaryShortCutStr = 'Ctrl+-'
      ShortCutStr = 'Ctrl+Num -'
    end
    object ZoomActualAction: TUiAction
      Category = 'View'
      Caption = '&Actual Size'
      Hint = 'Actual Size|Makes pictures appear in their actual size.'
      ImageIndex = imgPixZoomActual
    end
    object ZoomFitAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Fit to Window'
      Hint = 'Fit to Window|Makes pictures appear to fill panes.'
      ImageIndex = imgPixZoomFit
    end
  end
  object Tree: TUiActionTree
    Nodes = ('View: Menu', ('DiffTolerance: MenuItem', 'DiffRange: MenuItem', 'DiffBlend: MenuItem', 'DisplayFilters: SeparatorItem', 'SameModIgnored: MenuItem', 'AutoScale: MenuItem', 'RotateRight: MenuItem', 'RotateLeft: MenuItem', 'FlipHorz: MenuItem', 'FlipVert: MenuItem', 'OffsetReset: MenuItem', 'Display: SeparatorItem', 'CompareTags: MenuItem', 'Layout: SeparatorItem', 'BlendToggle: MenuItem', 'ShowSpecInfo: MenuItem', 'FullScreen: MenuItem', 'ZoomList: SubmenuItem', ('ZoomIn: MenuItem', 'ZoomOut: MenuItem', 'ZoomActual: MenuItem', 'ZoomFit: MenuItem')), 'Main: Toolbar', ('SessionLocked: ToolButton', 'DiffMode: SeparatorButton', 'DiffTolerance: ToolButton', 'DiffRange: ToolButton', 'DiffBlend: ToolButton', 'InsigIgnored: ToolButton', 'AutoScale: ToolButton', 'RotateRight: ToolButton', 'RotateLeft: ToolButton', 'FlipHorz: ToolButton', 'FlipVert: ToolButton', 'View: SeparatorButton', 'CompareTags: ToolButton', 'ShowSpecInfo: ToolButton', 'FullScreen: ToolButton'), 'ScrollBox: PopupMenu', ('Copy: MenuItem', 'N1: SeparatorItem', 'AutoScale: MenuItem', 'RotateRight: MenuItem', 'RotateLeft: MenuItem', 'FlipHorz: MenuItem', 'FlipVert: MenuItem', 'N2: SeparatorItem', 'FullScreen: MenuItem', 'N3: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem'), 'ExplorerList: SubmenuItem', ()), 'CenterScrollBox: PopupMenu', ('Copy: MenuItem', 'N1: SeparatorItem', 'OffsetReset: MenuItem', 'N2: SeparatorItem', 'FullScreen: MenuItem'), 'Edit: PopupMenu', ('Copy: MenuItem', 'N1: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem'), 'ExplorerList: SubmenuItem', ()))
  end
end
